"""Decision Time Machine v0 — counterfactual rulings, pure code.

Flip a business-rule conflict ruling and compute the structural blast radius
by re-deriving the amendment set deterministically: which requirements
rewrite, which launch conditions disappear, which rules would never be born.
Scores are NOT faked: the branch is labeled "re-grade required" because
grading is a model task. Everything shown is computed, not narrated.
"""

from engine.debate import apply_amendments
from engine.schemas import Amendment, AmendmentSet, DraftSpec


def alternative_branch(run: dict, conflict_id: str = "C1") -> dict | None:
    """Reverse the ruling on a business-rule conflict: the published policy
    wins instead of the decision-maker. Returns the counterfactual diff."""
    s = run["stages"]
    conflict = next((c for c in s["conflicts"]["conflicts"] if c["id"] == conflict_id), None)
    if not conflict or conflict["kind"] != "business-rule":
        return None

    arbiter = AmendmentSet.model_validate(s["debate"]["arbiter"])
    findings_for_conflict = {
        f["id"] for f in s["grade_round1"]["findings"] if f["evidence_ref"] == conflict_id
    }

    kept: list[Amendment] = []
    replaced: list[dict] = []
    for am in arbiter.amendments:
        if findings_for_conflict & set(am.finding_ids):
            alt = Amendment(
                requirement_id=am.requirement_id,
                finding_ids=am.finding_ids,
                before=am.before,
                after=("follow the human-adjuster review path required by the published "
                       "policy (section 4.1); automated approval is out of scope for v1"),
                rationale="COUNTERFACTUAL: the published policy wins; the decision-maker's "
                          "automation mandate is rejected.",
            )
            kept.append(alt)
            replaced.append({"requirement_id": am.requirement_id,
                             "original_after": am.after, "counterfactual_after": alt.after})
        else:
            kept.append(am)

    alt_set = AmendmentSet(
        amendments=kept,
        new_requirements=arbiter.new_requirements,
        unresolved_human_decisions=[
            d for d in arbiter.unresolved_human_decisions if conflict_id not in d
        ],
        summary=f"Counterfactual branch: ruling on {conflict_id} reversed.",
    )
    draft = DraftSpec.model_validate(s["draft_spec"])
    alt_spec = apply_amendments(draft, alt_set)

    removed_conditions = [d for d in arbiter.unresolved_human_decisions if conflict_id in d]
    return {
        "conflict_id": conflict_id,
        "what_if": "The published policy wins; automated approval is rejected for v1.",
        "requirements_rewritten": replaced,
        "launch_conditions_removed": removed_conditions,
        "rules_never_born": ["Published policy gates automated behavior (JR-001-class)"],
        "unchanged": [am.requirement_id for am in kept
                      if not (findings_for_conflict & set(am.finding_ids))],
        "alt_spec": alt_spec.model_dump(),
        "note": "Structural diff is computed. Scores require a re-grade (model task) — run live to score this branch.",
    }
