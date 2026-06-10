"""Generate the default demo run by executing the REAL pipeline with a
scripted LLM.

The content of each model call is curated (deterministic), but every engine
path is real: the gate runs as code, amendments are applied by the real
diff logic, the eval-log is the real append-only log. The run is labeled
kind="scripted-demo" in meta — run live mode with your own key for a fully
model-generated run.

Usage: .venv/bin/python scripts/make_demo_run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.llm import Usage  # noqa: E402
from engine.pipeline import run_pipeline, save_run  # noqa: E402

W = lambda sf, st, loc, sp, q: {  # noqa: E731
    "source_file": sf, "source_type": st, "locator": loc, "speaker": sp, "quote": q}

T1 = "transcript-01-founder-direction.md"
T2 = "transcript-02-claims-ops.md"
POL = "policy-claims-handling.md"
CODE = "code-claims-sla.py.txt"
DB = "db-claims-schema.sql"

WIKI = {
    "project_summary": "AnDigi v1 ships claims FNOL with AI triage: app-based filing, instant auto-approval for low-value clean claims, 48-hour payouts, risk-based e-KYC, and human investigators for fraud.",
    "claims": [
        {"id": "W1", "topic": "FNOL", "claim": "Customers file the loss in the app with photos, a description and the incident date.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 9", "CEO", "customers file the loss in the app — photos, a description, the incident date. No call centers.")]},
        {"id": "W2", "topic": "Auto-approval", "claim": "Claims under 5,000,000 VND that pass AI triage with no fraud flag are approved instantly with no human in the path.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 12", "CEO", "claims under 5 million VND that pass AI triage get auto-approved instantly. No human in that path.")]},
        {"id": "W3", "topic": "Payout SLA", "claim": "Approved claims pay out within 48 hours of the approval decision.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 22", "CEO", "Forty-eight hours from approval to money in the customer's account.")]},
        {"id": "W4", "topic": "e-KYC", "claim": "Identity is verified once at onboarding; re-verification happens only when a risk flag fires.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 27", "CEO", "Customers verify identity once at onboarding. We do not ask again unless a risk flag fires.")]},
        {"id": "W5", "topic": "e-KYC regulation", "claim": "No current regulation requires periodic re-verification of e-KYC for policyholders; re-verification is risk-based at the insurer's discretion.", "authority": "Ops statement", "claim_class": "fact",
         "sources": [W(T2, "transcript", "Compliance Officer, line 21", "Compliance Officer", "No current regulation requires periodic re-verification of e-KYC for policyholders.")]},
        {"id": "W6", "topic": "Fraud", "claim": "Any fraud flag routes to a human investigator; the AI never clears its own fraud flag.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 32", "CEO", "Any fraud flag routes to a human investigator, always. The AI never clears its own fraud flag.")]},
        {"id": "W7", "topic": "Fraud records", "claim": "Fraud investigation records are retained for ten years.", "authority": "Written policy", "claim_class": "fact",
         "sources": [W(POL, "doc", "Section 9.2", "", "Investigation records are retained for ten (10) years."),
                      W(T2, "transcript", "Compliance Officer, line 27", "Compliance Officer", "audit trail retained for ten years")]},
        {"id": "W8", "topic": "High-value claims", "claim": "Claims of 5,000,000 VND or more get a human adjuster decision within 3 business days.", "authority": "CEO decision", "claim_class": "decision",
         "sources": [W(T1, "transcript", "CEO, line 36", "CEO", "Human adjuster reviews, decision within 3 business days.")]},
        {"id": "W9", "topic": "Review policy", "claim": "The published claims policy requires a licensed human adjuster to review every claim before any payout decision.", "authority": "Written policy", "claim_class": "fact",
         "sources": [W(POL, "doc", "Section 4.1", "", "Every claim is reviewed by a licensed human adjuster before any payout decision is issued.")]},
        {"id": "W10", "topic": "Current practice", "claim": "Today every claim of any size goes through a human adjuster, and the team works to roughly a five-day payout turnaround.", "authority": "Ops statement", "claim_class": "fact",
         "sources": [W(T2, "transcript", "Claims Ops Lead, lines 9-16", "Claims Ops Lead", "today every claim, any size, goes through a human adjuster before payout … roughly a five-day turnaround after approval.")]},
        {"id": "W11", "topic": "Payout policy", "claim": "The published policy promises payout within 48 hours of approval.", "authority": "Written policy", "claim_class": "fact",
         "sources": [W(POL, "doc", "Section 5.1", "", "Approved claims are paid within 48 hours of the approval decision.")]},
        {"id": "W12", "topic": "Payout code", "claim": "Production code sets PAYOUT_SLA_HOURS = 120, i.e. five days from approval to disbursement.", "authority": "Artifact state", "claim_class": "artifact-state",
         "sources": [W(CODE, "code", "sla.py line 5", "", "PAYOUT_SLA_HOURS = 120  # 5 days from approval to disbursement")]},
        {"id": "W13", "topic": "Payout schema", "claim": "The claims table defaults payout_due_days to 5.", "authority": "Artifact state", "claim_class": "artifact-state",
         "sources": [W(DB, "db", "claims.payout_due_days", "", "payout_due_days INTEGER NOT NULL DEFAULT 5")]},
    ],
}

CONFLICTS = {
    "conflicts": [
        {"id": "C1", "kind": "business-rule", "claim_ids": ["W2", "W9", "W10"],
         "description": "The CEO mandates instant auto-approval with no human in the path for low-value claims, while the published claims policy (4.1) requires a human adjuster to review EVERY claim before payout — and current practice follows the policy.",
         "winning_claim_id": "W2", "winning_authority": "CEO decision",
         "resolution": "Spec implements auto-approval per W2, but the published policy is what auditors see: policy section 4.1 must be amended BEFORE launch, and that is a human decision, not a spec edit.",
         "needs_human_confirmation": True},
        {"id": "C2", "kind": "artifact-state-gap", "claim_ids": ["W3", "W11", "W12", "W13", "W10"],
         "description": "Intended payout SLA is 48 hours (CEO decision W3, policy 5.1 W11) but the system CURRENTLY pays in 5 days: code hard-codes PAYOUT_SLA_HOURS=120 (W12), the DB defaults payout_due_days=5 (W13), and ops works to ~5 days (W10).",
         "winning_claim_id": "W3", "winning_authority": "CEO decision",
         "resolution": "The 48-hour target stands; the 120-hour artifact state is a fact no one can out-talk. The gap becomes an explicit migration requirement (code + schema + open-claims backfill).",
         "needs_human_confirmation": False},
    ],
    "notes": "W4 vs W5 are aligned (once-at-onboarding + risk-based re-verification). W6/W7/W8 are consistent across transcript and policy. R3's 90-day re-verification claim has NO supporting claim anywhere in the corpus — that is a grading matter, not a conflict between sources.",
}

CHECK = lambda d, item, res, note="": {"dimension": d, "item": item, "result": res, "note": note}  # noqa: E731

GRADE1 = {
    "checklist": [
        CHECK("D1", "Every source decision is addressed by a requirement", "PASS"),
        CHECK("D1", "Conflict resolutions reflected in the draft", "FAIL", "C1: R2 ignores policy 4.1 conflict entirely; no policy-update precondition anywhere."),
        CHECK("D1", "Artifact-state gaps surfaced as migration work", "FAIL", "C2: 48h payout promised while code/DB enforce 5 days; no migration requirement exists."),
        CHECK("D2", "At least 3 edge cases beyond sources", "FAIL", "Only lapsed-policy edge in R1; no triage-service-down, no partial-photo, no payout-failure path."),
        CHECK("D2", "Failure path per major requirement", "FAIL", "R2 has no behavior for disbursement failure after instant approval."),
        CHECK("D3", "Every domain fact traces to a claim id", "FAIL", "R3 cites 'Circular 14/2026' — no such source exists in the corpus; W5 says the opposite."),
        CHECK("D3", "No invented numbers or SLAs", "PASS"),
        CHECK("D4", "Explicit out-of-scope present", "PASS"),
        CHECK("D5", "No hedge words / vague quantities", "FAIL", "R2: 'should disburse … promptly', 'processed quickly' — gate hits G1/G2 confirm."),
        CHECK("D5", "Acceptance criteria independently testable", "FAIL", "R2 AC2 unmeasurable; R5 prescribes Redis without [needs-dev-input] (gate G6)."),
    ],
    "findings": [
        {"id": "F1", "dimension": "D3", "priority": "P0", "requirement_id": "R3",
         "evidence_ref": "W5", "claim_class_violation": "regulatory-assumption without source",
         "description": "R3 invents a regulatory obligation ('Circular 14/2026', 90-day e-KYC re-verification). No source in the corpus supports it, and the Compliance Officer explicitly states no such regulation exists (W5). Shipping this creates fake compliance work and contradicts the CEO's onboarding-only decision (W4).",
         "suggested_fix": "Rewrite R3 to once-at-onboarding + risk-based re-verification per W4/W5; tag any residual regulatory doubt [needs-compliance-confirm].",
         "assigned_role": "compliance"},
        {"id": "F2", "dimension": "D1", "priority": "P1", "requirement_id": "R2",
         "evidence_ref": "C1", "claim_class_violation": "",
         "description": "R2's no-human auto-approval contradicts published policy 4.1 (W9) which auditors hold us to. The conflict is resolved by authority (CEO wins) but the spec must carry the launch precondition: policy amendment.",
         "suggested_fix": "Add a launch precondition AC: policy section 4.1 amended before auto-approval activates.",
         "assigned_role": "po"},
        {"id": "F3", "dimension": "D5", "priority": "P1", "requirement_id": "R2",
         "evidence_ref": "W3", "claim_class_violation": "",
         "description": "Payout timing is 'promptly'/'quickly' — untestable. The decided number exists: 48 hours (W3, W11).",
         "suggested_fix": "Replace with the explicit 48-hour bound, measured approval→disbursement.",
         "assigned_role": "qa"},
        {"id": "F4", "dimension": "D1", "priority": "P1", "requirement_id": "R2",
         "evidence_ref": "C2", "claim_class_violation": "",
         "description": "The system CURRENTLY enforces a 5-day payout (code W12, schema W13). Promising 48h without a migration requirement ships a broken promise.",
         "suggested_fix": "Add migration requirement: PAYOUT_SLA_HOURS 120→48, payout_due_days default 5→2, decide handling of in-flight claims.",
         "assigned_role": "eng"},
        {"id": "F5", "dimension": "D5", "priority": "P1", "requirement_id": "R5",
         "evidence_ref": "", "claim_class_violation": "recommendation stated as fact",
         "description": "R5 prescribes Redis — an implementation choice with no claim behind it (gate G6).",
         "suggested_fix": "Restate as a server-side session store requirement; tag the store choice [needs-dev-input].",
         "assigned_role": "sa"},
        {"id": "F6", "dimension": "D2", "priority": "P2", "requirement_id": "R1",
         "evidence_ref": "W1", "claim_class_violation": "",
         "description": "R1 lacks negative paths beyond lapsed policy: no photo-upload failure or duplicate-FNOL handling.",
         "suggested_fix": "Add duplicate-claim and upload-failure ACs.",
         "assigned_role": "ba"},
        {"id": "F9", "dimension": "D2", "priority": "P2", "requirement_id": "R1",
         "evidence_ref": "W1", "claim_class_violation": "",
         "description": "The lapsed-policy rejection (R1-AC2) is user-facing and terse: Vietnamese-first customers see raw text with no plain-language explanation or localization.",
         "suggested_fix": "Add an AC for localized, plain-language rejection copy with an in-app explainer.",
         "assigned_role": "ux"},
        {"id": "F10", "dimension": "D2", "priority": "P1", "requirement_id": "R2",
         "evidence_ref": "W2", "claim_class_violation": "",
         "description": "Instant auto-approval produces zero structured observability: no audit event, no cost attribution, no incident trail for an AI decision that moves money.",
         "suggested_fix": "Require a structured decision_event per triage to an immutable audit log.",
         "assigned_role": "devops"},
        {"id": "F11", "dimension": "D2", "priority": "P1", "requirement_id": "R4",
         "evidence_ref": "W6", "claim_class_violation": "",
         "description": "The fraud path assigns an investigator but defines no access control, redaction, or access logging for claim descriptions and photos passed downstream.",
         "suggested_fix": "Redact investigator tickets; gate full payloads behind RBAC with access logging.",
         "assigned_role": "security"},
        {"id": "F12", "dimension": "D4", "priority": "P2", "requirement_id": "R3",
         "evidence_ref": "", "claim_class_violation": "",
         "description": "Deferred P2 items and the two unresolved human decisions carry silently into sprint planning with no readiness list.",
         "suggested_fix": "Surface an explicit launch-readiness / known-open-items section in the corrected spec.",
         "assigned_role": "sm"},
    ],
    "scores": {"D1": 45, "D2": 40, "D3": 35, "D4": 85, "D5": 50},
    "overall_score": 61,
    "verdict": "NEEDS_REVISION",
}

RT = lambda issue, roles, q, close=False, net="": {  # noqa: E731
    "issue_id": issue, "summoned_roles": roles, "focused_question": q,
    "close_phase": close, "net_movement": net}

TURN = lambda obs, refs, risk, change, conf, assume, stance, msg, trefs: {  # noqa: E731
    "work_notes": {"observation": obs, "evidence_refs": refs, "risk": risk,
                    "proposed_change": change, "confidence": conf, "open_assumption": assume},
    "stance": stance, "message": msg, "refs": trefs}

DEBATE_SCRIPT = [
    # ---- phase: product (po, ba, ux) ----
    ("RouterDecision", RT("F2", ["po", "ba"],
        "R2 activates no-human auto-approval while published policy 4.1 requires human review of every claim. What must the spec carry so launch does not contradict the audited policy?")),
    ("Turn", TURN(
        "Compared R2 against policy 4.1 (W9) and the CEO decision (W2); checked C1 resolution.",
        ["F2", "C1", "W2", "W9"],
        "Auditors hold us to the published policy, not to meeting decisions.",
        "Add launch-precondition AC to R2: policy 4.1 amended before auto-approval activates.",
        "high", "CEO will approve the policy amendment quickly.",
        "concede",
        "F2 stands. The CEO decision wins inside the product, but the regulator reads policy 4.1, not our transcript. I am adding a launch precondition to R2: auto-approval stays dark until the published policy is amended. The policy change itself is a CEO/legal action — I am putting it on the human decision list, not pretending a spec edit fixes it.",
        ["F2", "R2", "C1"])),
    ("Turn", TURN(
        "Traced R2's ACs for coverage of the C1 precondition and operational fallback.",
        ["F2", "W10"],
        "If the precondition slips, ops silently falls back to manual review with no stated SLA.",
        "Fallback AC: while the precondition is unmet, claims under 5M follow R6's human review path.",
        "medium", "",
        "challenge",
        "Conceding the precondition is not enough: specify what happens while it is unmet. Today's practice (W10) is human review — so R2 needs an explicit fallback AC: until policy 4.1 is amended, sub-5M claims route through the R6 adjuster path. Otherwise launch day becomes an undefined state.",
        ["F2", "R2", "R6"])),
    ("RouterDecision", RT("F9", ["ux"],
        "The lapsed-policy rejection is user-facing and terse. What must R1 carry so a Vietnamese-first customer understands why they were rejected?")),
    ("Turn", TURN(
        "Walked the R1 rejection path as a first-time customer reading the lapse message.",
        ["F9", "W1"],
        "A raw rejection with no explanation reads as a broken app, not a lapsed policy.",
        "AC on R1: localized plain-language rejection copy + an in-app 'what this means / how to reinstate' explainer.",
        "high", "",
        "challenge",
        "F9: the rejection a customer sees IS the product in that moment. R1 needs an AC for localized, plain-language copy — state the lapse reason, what it means, and the reinstatement path — Vietnamese first, English fallback. Raw error strings to a customer who just had an accident is how trust dies in one screen.",
        ["F9", "R1"])),
    ("RouterDecision", RT("", [], "", True,
        "R2 gains a policy-amendment launch precondition and a manual-review fallback; R1 gains a localized rejection-copy AC. The policy change itself is escalated to the human decision list.")),
    # ---- phase: architecture (sa, eng) ----
    ("RouterDecision", RT("F4", ["sa", "eng"],
        "Code and schema enforce a 5-day payout while the spec promises 48 hours. Define the migration requirement that closes C2.")),
    ("Turn", TURN(
        "Read sla.py (W12) and claims schema default (W13); mapped every consumer of payout_due_days.",
        ["F4", "C2", "W12", "W13"],
        "Changing the constant without backfilling in-flight claims creates two SLA regimes silently.",
        "Migration req: code 120→48h, schema default 5→2, explicit decision on in-flight claims.",
        "high", "No other service hard-codes the 5-day assumption.",
        "challenge",
        "F4 is real and bigger than a constant: PAYOUT_SLA_HOURS=120 (sla.py:5) and payout_due_days DEFAULT 5 are artifact state — they will out-vote the spec at runtime. The migration requirement must cover code, schema default, and a stated rule for claims approved before cutover. Without the third item we change the promise mid-flight for open claims.",
        ["F4", "C2", "R2"])),
    ("Turn", TURN(
        "Checked disbursement path for idempotency under the tighter 48h window.",
        ["F4", "W3"],
        "Faster SLA means retries fire sooner; duplicate disbursement on retry is real money.",
        "One payout per claim id, enforced server-side; failure path AC on R2.",
        "high", "",
        "challenge",
        "Supporting the migration with one addition: at 48 hours the retry window compresses, so disbursement must be idempotent — exactly one payout per claim id enforced server-side — and R2 needs a failure-path AC for when disbursement fails after instant approval. Otherwise speed converts directly into double-payment risk.",
        ["F4", "R2"])),
    ("RouterDecision", RT("", [], "", True,
        "C2 becomes migration requirement R7 (code 120→48h, schema default 5→2, in-flight claims rule) plus idempotent disbursement and a failure-path AC on R2. Artifact state and promise now converge by construction.")),
    # ---- phase: quality (qa, devops) ----
    ("RouterDecision", RT("F3", ["qa"],
        "R2's payout wording is untestable ('promptly', 'quickly'). Fix the measurability.")),
    ("Turn", TURN(
        "Tested R2 ACs for measurability; cross-checked the decided bound in W3/W11.",
        ["F3", "W3", "W11"],
        "'Quickly' cannot fail a test, so it cannot pass one either.",
        "Bound: disbursement completes ≤48h from approval timestamp; measured field-to-field.",
        "high", "",
        "challenge",
        "F3: 'promptly' and 'quickly' are unfalsifiable. The decided number exists — 48 hours (W3, policy 5.1). The AC must read: payout completes within 48 hours of approval, measured approved_at → paid_at. That also gives the migration in R7 its acceptance test for free.",
        ["F3", "R2"])),
    ("RouterDecision", RT("F10", ["devops"],
        "An AI decision that moves money currently emits no structured trail. What observability must R2 require?")),
    ("Turn", TURN(
        "Traced the auto-approval path for audit events; found none between triage and disbursement.",
        ["F10", "W2"],
        "An unobservable money-moving decision is an incident investigation nightmare and an audit gap.",
        "Require decision_event {claim_id, triage_score, fraud_flag, latency, engine_version} to an immutable log, 90-day queryable, no PII in payload.",
        "high", "",
        "challenge",
        "F10: every instant approval must emit a structured decision_event — claim id, triage score, fraud flag, latency, engine version — to an immutable audit log, queryable for 90 days, with no PII in the payload. Without it, the first regulator question ('why did the AI approve this claim?') has no answer, and the first incident has no trail.",
        ["F10", "R2"])),
    ("RouterDecision", RT("", [], "", True,
        "R2's payout language becomes the explicit 48-hour bound measured approved_at→paid_at, and every triage decision now emits a structured audit event. No open quality findings remain.")),
    # ---- phase: risk (compliance, security) ----
    ("RouterDecision", RT("F1", ["compliance"],
        "R3 cites 'Circular 14/2026' requiring 90-day e-KYC re-verification. No source in the corpus supports it. Rule on it.")),
    ("Turn", TURN(
        "Searched the corpus for any source behind 'Circular 14/2026'; found none. W5 states the opposite.",
        ["F1", "W4", "W5"],
        "An invented regulatory obligation in a published spec is audit poison and blocks claims for no legal reason.",
        "Rewrite R3: verify once at onboarding, risk-based re-verification; tag residual doubt [needs-compliance-confirm].",
        "high", "",
        "challenge",
        "F1 is the worst kind of error: a confident, invented regulation. No 'Circular 14/2026' exists in our corpus; the Compliance Officer's statement (W5) and the CEO decision (W4) both say verification is once-at-onboarding with risk-based re-checks. R3 must be rewritten to that rule. If product believes a real circular exists, the burden is a citation — until then the claim carries [needs-compliance-confirm] and nothing is blocked on a 90-day clock.",
        ["F1", "R3"])),
    ("RouterDecision", RT("F11", ["security"],
        "Fraud-flagged claims route descriptions and photos to investigators. What protects that sensitive payload?")),
    ("Turn", TURN(
        "Followed a fraud-flagged claim payload from triage to the investigator ticket.",
        ["F11", "W6", "W7"],
        "Full descriptions and photos in tickets leak sensitive data to anyone with queue access.",
        "Redacted ticket (<=80-char summary + claim id); full payload behind RBAC with access logging; fraud flag immutable once set.",
        "high", "",
        "challenge",
        "F11: the investigator ticket must carry a redacted summary and the claim id only; the full description and photos sit behind role-based access with every view logged. And the fraud flag is immutable once set — neither the customer, the agent, nor the AI clears it; only the named investigator closes it with a recorded decision (W6, retention per W7).",
        ["F11", "R4"])),
    ("RouterDecision", RT("", [], "", True,
        "The invented 90-day obligation is removed and R3 rewritten to risk-based re-verification; the fraud path gains redaction, RBAC with access logging, and an immutable flag. P0 grounding failure resolved.")),
    ("RouterDecision", RT("F12", ["sm"],
        "Deferred P2s and two human decisions remain open. What must the spec surface so sprint planning has no surprises?")),
    ("Turn", TURN(
        "Collected every deferred item and open decision across the four phases.",
        ["F12", "F6", "F9"],
        "Silent carry-over is how sprint 1 inherits invisible risk and blows its commitment.",
        "Add an explicit launch-readiness section: open decisions with owners, deferred P2s, and the policy precondition status.",
        "medium", "",
        "challenge",
        "F12: the corrected spec must end with a launch-readiness list — the two human decisions with owners, the deferred P2s (upload-failure paths, localization backlog), and the policy-amendment precondition status. Sprint planning reads that list, not the whole debate. No invisible carry-over.",
        ["F12", "R3", "R1"])),
    ("RouterDecision", RT("", [], "", True,
        "All deferred items and open decisions are consolidated into an explicit launch-readiness list with owners. Synthesis hands a clean state to the arbiter.")),
    # ---- arbiter ----
    ("AmendmentSet", {
        "amendments": [
            {"requirement_id": "R2", "finding_ids": ["F3"],
             "before": "and the system should disburse the payout promptly after approval",
             "after": "and the payout is disbursed within 48 hours of approval [W3, policy 5.1]",
             "rationale": "Replaces hedge + vague timing with the decided, testable bound."},
            {"requirement_id": "R2", "finding_ids": ["F3", "F4"],
             "before": "the payout will be processed quickly",
             "after": "the payout completes within 48 hours of approval, measured from approved_at to paid_at, with exactly one disbursement per claim id enforced server-side",
             "rationale": "Measurable bound + idempotency from the architecture phase."},
            {"requirement_id": "R2", "finding_ids": ["F2"],
             "before": "are auto-approved instantly",
             "after": "are auto-approved instantly once policy section 4.1 is amended to permit automated approval (launch precondition); until then they follow the R6 human-review path",
             "rationale": "Carries the C1 resolution: the published policy must change before the behavior ships."},
            {"requirement_id": "R3", "finding_ids": ["F1"],
             "before": "Per Circular 14/2026 on digital insurance distribution, customer e-KYC data must be re-verified every 90 days, and claims from customers with expired verification are held until re-verification completes.",
             "after": "Customer e-KYC is verified once at onboarding; re-verification is triggered only by risk indicators [W4, W5, policy 7.1-7.2]. [needs-compliance-confirm: no periodic re-verification obligation exists in the evidence corpus]",
             "rationale": "Removes an invented regulatory obligation contradicted by the corpus."},
            {"requirement_id": "R5", "finding_ids": ["F5"],
             "before": "Triage session tokens are stored in Redis with a 30-minute TTL",
             "after": "Triage session state persists server-side with a 30-minute TTL [needs-dev-input: storage choice]",
             "rationale": "Removes an unsourced implementation prescription; the choice belongs to engineering."},
        ],
        "new_requirements": [
            {"id": "R7", "title": "Payout SLA migration (artifact-state gap C2)",
             "statement": "Engineering migrates the payout SLA from the current 5-day artifact state to the decided 48-hour bound: PAYOUT_SLA_HOURS 120 to 48 in sla.py, claims.payout_due_days default 5 to 2, and claims approved before cutover keep their original deadline.",
             "acceptance_criteria": [
                 "Given the migration is deployed, when a claim is approved, then its payout deadline is 48 hours after approved_at.",
                 "Given a claim approved before cutover, when deadlines are computed, then the original 120-hour deadline applies.",
                 "Given the schema migration runs, when a new claim row is created, then payout_due_days defaults to 2."],
             "source_claim_ids": ["W3", "W11", "W12", "W13"]},
        ],
        "unresolved_human_decisions": [
            "Policy section 4.1 contradicts the CEO's no-human auto-approval decision (C1). Amending the published, audited policy is a CEO/legal action and a LAUNCH PRECONDITION — the spec cannot resolve it.",
            "Confirm with the regulator-facing counsel that no periodic e-KYC re-verification obligation exists (R3 carries [needs-compliance-confirm] until then).",
        ],
        "summary": "Five amendments and one new migration requirement: the invented regulation is removed, the payout promise becomes a measured 48-hour bound with idempotent disbursement, the policy conflict becomes an explicit launch precondition, and the code/DB artifact gap becomes requirement R7. Two decisions remain deliberately human.",
    }),
    # ---- grade round 2 ----
    ("GradeReport", {
        "checklist": [
            CHECK("D1", "Every source decision is addressed by a requirement", "PASS"),
            CHECK("D1", "Conflict resolutions reflected in the draft", "PASS"),
            CHECK("D1", "Artifact-state gaps surfaced as migration work", "PASS", "R7 covers code, schema and in-flight claims."),
            CHECK("D2", "At least 3 edge cases beyond sources", "PASS", "Fallback path, in-flight claims, disbursement failure/idempotency, audit events, redacted fraud tickets."),
            CHECK("D2", "Failure path per major requirement", "FAIL", "R1 still lacks upload-failure and duplicate-FNOL paths (P2, deferred)."),
            CHECK("D3", "Every domain fact traces to a claim id", "FAIL", "R3 still carries empty source links pending compliance confirmation (P2, tagged)."),
            CHECK("D3", "No invented numbers or SLAs", "PASS"),
            CHECK("D4", "Explicit out-of-scope present", "PASS"),
            CHECK("D5", "No hedge words / vague quantities", "PASS", "Gate round 2 confirms G1/G2 clear."),
            CHECK("D5", "Acceptance criteria independently testable", "PASS"),
        ],
        "findings": [
            {"id": "F7", "dimension": "D2", "priority": "P2", "requirement_id": "R1",
             "evidence_ref": "W1", "claim_class_violation": "",
             "description": "Upload-failure and duplicate-FNOL negative paths still missing (carried from F6).",
             "suggested_fix": "Add both ACs in the next revision.", "assigned_role": "ba"},
            {"id": "F8", "dimension": "D3", "priority": "P2", "requirement_id": "R3",
             "evidence_ref": "W5", "claim_class_violation": "",
             "description": "R3's [needs-compliance-confirm] tag is correct but its source links stay empty until counsel confirms.",
             "suggested_fix": "Attach the confirmation note as a source when it arrives.", "assigned_role": "compliance"},
        ],
        "scores": {"D1": 95, "D2": 85, "D3": 90, "D4": 95, "D5": 95},
        "overall_score": 92,
        "verdict": "SATISFIED_WITH_DEFERRED",
    }),
    # ---- advisor ----
    ("AdvisorReport", {
        "items": [
            {"severity": "S1",
             "concern": "Fraud investigations (R4) have a retention rule but no decision SLA — investigations can age indefinitely while a customer waits.",
             "suggestion": "Consider a time-bound: investigator decision within N business days, N decided with claims ops."},
            {"severity": "S2",
             "concern": "FNOL rejection copy (lapsed policy, R1) is user-facing and Vietnamese-first users will see it verbatim.",
             "suggestion": "Add localized, plain-language rejection messages to the UX backlog."},
        ],
        "verdict": "MINOR_POLISH",
    }),
]


class ScriptedLLM:
    """Deterministic stand-in: pops curated responses in pipeline call order."""

    model = "scripted/deterministic"
    base_url = "-"
    token_budget = 150_000

    def __init__(self):
        self.usage = Usage()
        self._queue = [("Wiki", WIKI), ("ConflictReport", CONFLICTS), ("GradeReport", GRADE1)] \
            + list(DEBATE_SCRIPT)

    def complete_json(self, system, user, schema, on_text=None):
        name, payload = self._queue.pop(0)
        assert schema.__name__ == name, f"call order broke: expected {name}, engine asked {schema.__name__}"
        obj = schema.model_validate(payload)
        if on_text:
            for ch in getattr(obj, "message", "")[:0]:  # no fake streaming in scripted runs
                on_text(ch)
        return obj


def main() -> None:
    llm = ScriptedLLM()
    run = run_pipeline(llm)
    run["meta"]["kind"] = "scripted-demo"
    run["meta"]["note"] = (
        "Deterministic scripted content executed through the REAL engine "
        "(real code gate, real amendment application, real eval-log). "
        "Run live mode with your own key for a fully model-generated run."
    )
    path = save_run(run, "demo-andigi")
    g1 = run["stages"]["grade_round1"]["overall_score"]
    g2 = run["stages"]["grade_round2"]["overall_score"]
    print(f"saved {path} | gate errors r1={run['stages']['gate']['errors']} "
          f"r2={run['stages']['gate_round2']['errors']} | score {g1} -> {g2} | "
          f"turns={len(run['stages']['debate']['turns'])} | events={len(run['events'])}")


if __name__ == "__main__":
    main()
