"""Release Baseline handoff artifacts — pure generators, no LLM.

Everything cites receipts: requirements carry their claim ids, tickets carry
verbatim evidence quotes, decisions carry the human's exact ruling text.
"""

import time

from engine import team


def baseline_id() -> str:
    return f"BL-{time.strftime('%Y%m%d-%H%M')}"


def _claims_by_id(run: dict) -> dict:
    return {c["id"]: c for c in run["stages"]["wiki"]["claims"]}


def signed_spec_md(run: dict, signoff: dict) -> str:
    spec = run["stages"]["corrected_spec"]
    g2 = run["stages"]["grade_round2"]
    lines = [
        f"# {spec['feature_name']} — Signed specification",
        "",
        f"Baseline: **{signoff['baseline_id']}** · signed {signoff['signed_at']} by {signoff['by']}",
        f"Readiness {g2['overall_score']}/100 · verdict {g2['verdict']} · "
        f"{len(signoff['rulings'])} human rulings · {len(signoff['rules_approved'])} rules distilled",
        "",
        spec["summary"],
        "",
        "## Requirements",
    ]
    for req in spec["requirements"]:
        lines += ["", f"### {req['id']} — {req['title']}", "", req["statement"], ""]
        lines += [f"- AC: {ac}" for ac in req["acceptance_criteria"]]
        lines += [f"- Evidence: {', '.join(req['source_claim_ids']) or 'tagged assumption'}"]
    lines += ["", "## Out of scope"] + [f"- {o}" for o in spec["out_of_scope"]]
    lines += ["", "## Human rulings (permanent record)"]
    for r in signoff["rulings"]:
        lines += ["", f"- **Decision:** {r['decision_text']}",
                  f"  - **Ruling:** {r['choice']}",
                  f"  - **Rationale:** {r['rationale'] or '—'}"]
    return "\n".join(lines)


def decision_record_md(run: dict, signoff: dict) -> str:
    lines = [
        f"# Decision record — {signoff['baseline_id']}",
        "",
        f"Signed {signoff['signed_at']} by {signoff['by']}.",
        "",
        "## Rulings",
    ]
    for r in signoff["rulings"]:
        lines += ["", f"### {r['decision_text']}", f"- Ruling: **{r['choice']}**",
                  f"- Rationale: {r['rationale'] or '—'}"]
    lines += ["", "## Amendment reviews"]
    amendments = run["stages"]["debate"]["arbiter"]["amendments"]
    for rv in signoff["reviews"]:
        am = amendments[rv["amendment_index"]]
        lines += ["", f"### {am['requirement_id']}: {rv['action'].upper()}",
                  f"- Arbiter proposal: {am['after'][:160]}"]
        if rv["action"] == "edit":
            lines += [f"- Human text: {rv['edited_after']}"]
        if rv.get("rationale"):
            lines += [f"- Rationale: {rv['rationale']}"]
    lines += ["", "## Rules distilled"] + [f"- {rid}" for rid in signoff["rules_approved"]] or ["- none"]
    return "\n".join(lines)


def ticket_stubs_md(run: dict, signoff: dict) -> str:
    spec = run["stages"]["corrected_spec"]
    claims = _claims_by_id(run)
    findings = {f["id"]: f for f in run["stages"]["grade_round1"]["findings"]}
    debate_roles: dict[str, str] = {}
    for t in run["stages"]["debate"]["turns"]:
        for ref in t.get("refs", []):
            debate_roles.setdefault(ref, t["role"])

    lines = [f"# Ticket stubs — {signoff['baseline_id']} (Jira/Linear-ready markdown)"]
    for req in spec["requirements"]:
        owner_role = debate_roles.get(req["id"], "eng")
        lines += ["", "---", "", f"## [{req['id']}] {req['title']}", "", req["statement"], "",
                  "**Acceptance criteria**"]
        lines += [f"- [ ] {ac}" for ac in req["acceptance_criteria"]]
        evid = [claims[cid] for cid in req["source_claim_ids"] if cid in claims][:2]
        if evid:
            lines += ["", "**Evidence**"]
            for c in evid:
                src = c["sources"][0]
                lines += [f"> {src['quote']} — {src['source_file']} · {src['locator']}"]
        lines += ["", f"**Suggested owner:** {team.role_label(owner_role)}"]
        rel = [f for f in findings.values() if f["requirement_id"] == req["id"] and f["priority"] == "P0"]
        if rel:
            lines += [f"**P0 history:** {rel[0]['description'][:140]}"]
    lines += ["", "---", "", "## Launch blockers (human decisions)"]
    for r in signoff["rulings"]:
        lines += ["", f"- **{r['choice']}** — {r['decision_text'][:140]} (rationale: {r['rationale'] or '—'})"]
    return "\n".join(lines)
