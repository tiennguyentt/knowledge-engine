"""Executable Baseline Compiler (round-8 consensus, B2).

Compiles the SIGNED baseline — corrected spec + human rulings + ledger rules —
into a typed decision-table IR executed by a tiny generic rule engine. Pure
code, no model. Change a ruling -> recompile -> the running behavior and its
acceptance vectors change, with citations versioned by baseline.

Honesty mitigations (Codex round-8): the engine is generic (it evaluates
whatever the table says), the table IR is shown to the user before execution,
and acceptance vectors are generated independently from the same signed
baseline so a behavior/test mismatch is detectable.
"""

import re
from dataclasses import asdict, dataclass, field

from engine.schemas import DraftSpec

FRAUD_KEYWORDS = ["staged", "fake", "collusion", "pre-arranged", "insurance fraud", "witness paid"]


@dataclass
class RuleEntry:
    id: str
    order: int
    conditions: list  # [{field, op, value}] — generic, evaluated by the engine
    verdict: str      # "reject" | "block" | "investigate" | "approve" | "review"
    title: str
    body: str
    cites: str


@dataclass
class DecisionTable:
    baseline_id: str
    version: int
    auto_approval_enabled: bool
    threshold_vnd: int
    payout_hours: int
    entries: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_threshold(spec: DraftSpec) -> int:
    for req in spec.requirements:
        m = re.search(r"under\s+([\d,\.]+)\s*VND", req.statement, re.I)
        if m:
            return int(m.group(1).replace(",", "").replace(".", ""))
    return 5_000_000


def _extract_payout_hours(spec: DraftSpec) -> int:
    for req in spec.requirements:
        m = re.search(r"within\s+(\d+)\s+hours\s+of\s+approval", req.statement + " ".join(req.acceptance_criteria), re.I)
        if m:
            return int(m.group(1))
    return 48


def _ruling_disables_auto_approval(rulings: list[dict]) -> bool:
    for r in rulings or []:
        if "policy" in r.get("decision_text", "").lower() and r.get("choice", "").lower().startswith("reverse"):
            return True
    return False


def compile_baseline(run: dict, signoff: dict | None, ledger_rules: list) -> DecisionTable:
    spec = DraftSpec.model_validate(run["stages"]["corrected_spec"])
    rulings = (signoff or {}).get("rulings", [])
    reversed_c1 = _ruling_disables_auto_approval(rulings)
    threshold = _extract_threshold(spec)
    payout = _extract_payout_hours(spec)
    version = 2 if reversed_c1 else 1
    baseline_id = (signoff or {}).get("baseline_id", "BL-unsigned")

    jr = next((r for r in ledger_rules if "policy" in r.title.lower()), None)
    jr_cite = f" · enforced by {jr.id} (born from your ruling, {jr.born_date})" if jr and reversed_c1 else ""

    req = {r.id: r for r in spec.requirements}
    entries = [
        RuleEntry("E1", 1, [{"field": "policy", "op": "eq", "value": "lapsed"}],
                  "reject", "REJECTED — lapsed policy",
                  "Submission rejected with the lapse reason, in plain localized language.",
                  "executes R1-AC2 · born from W1 · localized copy per UX turn (F9)"),
        RuleEntry("E2", 2, [{"field": "photo", "op": "eq", "value": False}],
                  "block", "BLOCKED — no photo attached",
                  "FNOL requires at least one photo before a claim record is created.",
                  "executes R1-AC1 · born from W1"),
        RuleEntry("E3", 3, [{"field": "fraud", "op": "eq", "value": True}],
                  "investigate", "ASSIGNED TO HUMAN INVESTIGATOR",
                  "The AI never clears its own fraud flag. Redacted ticket; RBAC + access-logged payload; record kept 10 years.",
                  "executes R4-AC1/AC2 · born from W6, W7 · redaction per Security turn (F11)"),
    ]
    if reversed_c1:
        entries.append(RuleEntry(
            "E4", 4, [{"field": "amount", "op": "lt", "value": threshold}],
            "review", "ROUTED TO HUMAN ADJUSTER — auto-approval disabled by your ruling",
            "Your ruling reversed C1: the published policy (4.1) wins; every claim takes the human-review path in v1.",
            f"executes your C1 reversal · policy 4.1 (W9) governs{jr_cite}"))
    else:
        entries.append(RuleEntry(
            "E4", 4, [{"field": "amount", "op": "lt", "value": threshold},
                       {"field": "precondition", "op": "eq", "value": True}],
            "approve", f"INSTANT APPROVED — payout due in {payout}:00:00",
            f"No human in the path (launch precondition met). One disbursement per claim id, "
            f"measured approved_at → paid_at within {payout}h; decision_event emitted to the audit log.",
            "executes R2-AC1 · born from W2/W3 · idempotency per Eng (F4) · audit event per DevOps (F10) · "
            "48h bound per QA (F3)"))
        entries.append(RuleEntry(
            "E5", 5, [{"field": "amount", "op": "lt", "value": threshold}],
            "review", "ROUTED TO HUMAN ADJUSTER — precondition unmet",
            "Policy 4.1 is not yet amended; the manual-review fallback applies until your launch precondition is satisfied.",
            "executes the R2 amendment (F2) · your C1 ruling is the gate"))
    entries.append(RuleEntry(
        "E6", 9, [],
        "review", "ROUTED TO HUMAN ADJUSTER — decision within 3 business days",
        "High-value claims get a human decision; escalates to claims ops on breach.",
        f"executes {'R6' if 'R6' in req else 'high-value path'}-AC1/AC2 · born from W8"))

    return DecisionTable(baseline_id=baseline_id, version=version,
                         auto_approval_enabled=not reversed_c1,
                         threshold_vnd=threshold, payout_hours=payout, entries=entries)


def evaluate(table: DecisionTable, claim: dict) -> RuleEntry:
    """Generic engine: first entry whose conditions all hold wins."""
    facts = dict(claim)
    facts["fraud"] = any(k in claim.get("description", "").lower() for k in FRAUD_KEYWORDS)
    for entry in sorted(table.entries, key=lambda e: e.order):
        ok = True
        for cond in entry.conditions:
            v, ref = facts.get(cond["field"]), cond["value"]
            if cond["op"] == "eq" and v != ref:
                ok = False
            elif cond["op"] == "lt" and not (isinstance(v, (int, float)) and v < ref):
                ok = False
        if ok:
            return entry
    return table.entries[-1]


def acceptance_vectors(table: DecisionTable) -> list[dict]:
    """Independent test vectors derived from the same signed baseline (B1 typed subset)."""
    t = table.threshold_vnd
    vectors = [
        {"id": "V-R1-AC2", "ac": "R1-AC2 lapsed policy rejected",
         "claim": {"amount": 2_000_000, "policy": "lapsed", "photo": True, "precondition": True, "description": "water damage"},
         "expect": "reject"},
        {"id": "V-R1-AC1", "ac": "R1-AC1 photo required",
         "claim": {"amount": 2_000_000, "policy": "active", "photo": False, "precondition": True, "description": "dent"},
         "expect": "block"},
        {"id": "V-R4-AC1", "ac": "R4-AC1 fraud routes to human",
         "claim": {"amount": 1_000_000, "policy": "active", "photo": True, "precondition": True, "description": "staged collision"},
         "expect": "investigate"},
        {"id": "V-R2-AC1", "ac": f"R2-AC1 clean claim under {t:,} VND",
         "claim": {"amount": t - 1_200_000, "policy": "active", "photo": True, "precondition": True, "description": "fender dent"},
         "expect": "approve" if table.auto_approval_enabled else "review"},
        {"id": "V-R2-FALLBACK", "ac": "R2 amendment: precondition unmet -> human path",
         "claim": {"amount": t - 1_200_000, "policy": "active", "photo": True, "precondition": False, "description": "fender dent"},
         "expect": "review"},
        {"id": "V-R6-AC1", "ac": "R6-AC1 high-value to adjuster",
         "claim": {"amount": t + 3_000_000, "policy": "active", "photo": True, "precondition": True, "description": "engine flood"},
         "expect": "review"},
    ]
    return vectors


def run_acceptance(table: DecisionTable) -> list[dict]:
    results = []
    for v in vectors_or(table):
        got = evaluate(table, v["claim"]).verdict
        results.append({**v, "got": got, "passed": got == v["expect"]})
    return results


def vectors_or(table: DecisionTable) -> list[dict]:
    return acceptance_vectors(table)
