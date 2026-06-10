"""Phase-gated, router-driven debate (v2).

Deterministic skeleton: five fixed concern phases with fixed role
eligibility (engine/team.yaml). Inside a phase, a bounded router call picks
the highest-value open finding and summons 1-3 eligible roles with a focused
question; max 2 router iterations per phase; a 2-sentence net-movement
summary closes each phase. Roles summoned for nothing emit a zero-token
"no objection" status. The arbiter synthesizes amendments at the end.

Every speaking turn must reference at least one open issue id. The debate
runs ONCE per pipeline run, between grading rounds.
"""

from collections.abc import Callable

from engine import team
from engine.llm import LLM
from engine.schemas import AmendmentSet, ConflictReport, DraftSpec, Finding, RouterDecision, Turn, Wiki

OnEvent = Callable[[dict], None]  # receives debate events for live UI

ROUTER_SYSTEM = """\
You are the debate router (process only - you decide WHO speaks about WHAT,
never the technical answer). Given the current phase, its eligible roles and
the open findings, pick the single highest-value unresolved finding for THIS
phase's concern, summon the 1-3 eligible roles with real standing on it, and
phrase the exact question they must answer. If no open finding fits this
phase, or the phase's findings are resolved, set close_phase=true and write
the 2-sentence net_movement summary. Never summon a role without standing.
"""

ARBITER_SYSTEM = """\
You are the neutral Arbiter. From the debate transcript, the findings and the
conflict resolutions, synthesize the final ruling as concrete amendments:
exact before/after text per requirement, new migration requirements for every
artifact-state gap, and a list of decisions that genuinely belong to the
human (do NOT resolve those - state them crisply). Base every amendment on
what survived the debate, with finding ids attached.
"""


def _turn_system(role_key: str) -> str:
    r = team.role(role_key)
    return (
        f"You are the {r['label']} in a spec red-team debate. {r['brief']} "
        "First write your work notes (what you inspected, which claims, the "
        "risk you hold, your proposed change, confidence, open assumption). "
        "Then your public message: max 110 words, concrete, referencing the "
        "finding/requirement/claim ids you address. Stance 'challenge', "
        "'defend' or 'concede' - concede when the evidence beats you. Never "
        "repeat an argument already made."
    )


def run_debate(
    llm: LLM,
    wiki: Wiki,
    conflicts: ConflictReport,
    spec: DraftSpec,
    findings: list[Finding],
    on_event: OnEvent | None = None,
    on_text: Callable[[str], None] | None = None,
) -> dict:
    lim = team.limits()
    emit = on_event or (lambda e: None)

    context = (
        f"WIKI (ground truth):\n{wiki.model_dump_json(indent=2)}\n\n"
        f"CONFLICT RESOLUTIONS:\n{conflicts.model_dump_json(indent=2)}\n\n"
        f"DRAFT SPEC:\n{spec.model_dump_json(indent=2)}"
    )

    open_findings = {f.id: f for f in findings}
    addressed: set[str] = set()
    phases_out: list[dict] = []
    turns_log: list[dict] = []

    for phase in team.phases():
        if phase["key"] == "synthesis":
            continue  # synthesis is the arbiter's job below
        phase_rec = {"key": phase["key"], "title": phase["title"],
                     "eligible": phase["eligible"], "events": []}
        emit({"type": "phase_start", "phase": phase["key"], "title": phase["title"]})

        spoke: set[str] = set()
        for iteration in range(1, lim["max_router_iterations_per_phase"] + 1):
            standing = [f.model_dump() for f in open_findings.values()
                        if f.id not in addressed and f.assigned_role in phase["eligible"]]
            decision = llm.complete_json(
                system=ROUTER_SYSTEM,
                user=(
                    f"PHASE: {phase['title']} (iteration {iteration} of "
                    f"{lim['max_router_iterations_per_phase']})\n"
                    f"ELIGIBLE ROLES: {phase['eligible']}\n"
                    f"OPEN FINDINGS FOR THIS PHASE:\n{standing}\n\n"
                    f"TURNS SO FAR:\n{[t['message'] for t in turns_log][-6:]}"
                ),
                schema=RouterDecision,
            )
            decision_d = decision.model_dump()
            decision_d["iteration"] = iteration
            phase_rec["events"].append({"type": "router", **decision_d})
            emit({"type": "router", "phase": phase["key"], **decision_d})

            if decision.close_phase or not standing:
                break

            summoned = [r for r in decision.summoned_roles
                        if r in phase["eligible"]][: lim["max_summoned_roles"]]
            for role_key in summoned:
                spoke.add(role_key)
                emit({"type": "turn_start", "phase": phase["key"], "role": role_key})
                turn = llm.complete_json(
                    system=_turn_system(role_key),
                    user=(
                        f"{context}\n\nFOCUSED QUESTION FROM THE ROUTER:\n"
                        f"{decision.focused_question}\n\n"
                        f"FINDING UNDER DEBATE:\n"
                        f"{open_findings[decision.issue_id].model_dump() if decision.issue_id in open_findings else decision.issue_id}\n\n"
                        f"DEBATE SO FAR:\n{[(t['role'], t['message']) for t in turns_log][-8:]}"
                    ),
                    schema=Turn,
                    on_text=on_text,
                )
                turn_d = {"phase": phase["key"], "role": role_key,
                          "issue_id": decision.issue_id, **turn.model_dump()}
                turns_log.append(turn_d)
                phase_rec["events"].append({"type": "turn", **turn_d})
                emit({"type": "turn", **turn_d})

            if decision.issue_id:
                addressed.add(decision.issue_id)

        # Roles eligible but never summoned: zero-token "no objection".
        for role_key in phase["eligible"]:
            if role_key not in spoke:
                ev = {"type": "no_objection", "phase": phase["key"], "role": role_key}
                phase_rec["events"].append(ev)
                emit(ev)

        phases_out.append(phase_rec)
        emit({"type": "phase_end", "phase": phase["key"]})

    arbiter = llm.complete_json(
        system=ARBITER_SYSTEM,
        user=(
            f"{context}\n\nALL FINDINGS:\n{[f.model_dump() for f in findings]}\n\n"
            f"DEBATE TRANSCRIPT:\n{[(t['role'], t['stance'], t['message']) for t in turns_log]}"
        ),
        schema=AmendmentSet,
    )
    emit({"type": "arbiter", "summary": arbiter.summary})

    return {"phases": phases_out, "turns": turns_log, "arbiter": arbiter.model_dump()}


def apply_amendments(spec: DraftSpec, amendments: AmendmentSet) -> DraftSpec:
    """Pure-python application of the arbiter's ruling to the draft."""
    data = spec.model_dump()
    for am in amendments.amendments:
        for req in data["requirements"]:
            if req["id"] != am.requirement_id:
                continue
            if am.before and am.before in req["statement"]:
                req["statement"] = req["statement"].replace(am.before, am.after)
            else:
                replaced = False
                for i, ac in enumerate(req["acceptance_criteria"]):
                    if am.before and am.before in ac:
                        req["acceptance_criteria"][i] = ac.replace(am.before, am.after)
                        replaced = True
                if not replaced and am.after:
                    req["acceptance_criteria"].append(am.after)
    for new_req in amendments.new_requirements:
        data["requirements"].append(new_req.model_dump())
    return DraftSpec.model_validate(data)
