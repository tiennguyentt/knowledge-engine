"""Deterministic quality gate — pure code, no model.

Runs BEFORE any model grading. Regex/structural checks over the draft spec.
Errors force the verdict path toward NEEDS_REVISION; the model layer cannot
override a gate hit. Ported (generic mechanics only) from a production
BA quality gate.
"""

import re
from dataclasses import asdict, dataclass, field

from engine.schemas import DraftSpec

GATE_VERSION = "v1.0"

HEDGE_WORDS = r"\b(should|might|possibly|ideally|perhaps|probably|likely)\b"
VAGUE_QUANTITIES = r"\b(a few|several|some|many|various|numerous|promptly|quickly|soon|as soon as possible)\b"
PASSIVE_FUTURE = r"\b(will be (handled|processed|managed|supported|stored|reviewed)|shall be|is being)\b"
FORBIDDEN_PATTERNS = r"(handle[sd]? .{0,30}appropriately|support all\b|update the database\b|similar to existing\b|improve the UX\b|system should validate)"
TECH_PRESCRIPTIONS = r"\b(INSERT INTO|SELECT FROM|CREATE TABLE|cron job|Redis|Kafka|RabbitMQ|DynamoDB)\b"
QUESTION_AT_END = r"\?\s*$"

RULES = {
    "G1": ("hedge-word", "error", HEDGE_WORDS, "Replace the hedge with a definite behavior."),
    "G2": ("vague-quantity", "error", VAGUE_QUANTITIES, "Replace with an explicit number or bound."),
    "G3": ("passive-future-voice", "warning", PASSIVE_FUTURE, "Rewrite in active voice: actor + verb + object."),
    "G4": ("forbidden-pattern", "error", FORBIDDEN_PATTERNS, "State the exact behavior instead of the vague phrase."),
    "G5": ("question-in-spec", "error", QUESTION_AT_END, "Resolve the question or move it to open decisions."),
    "G6": ("tech-prescription-untagged", "error", TECH_PRESCRIPTIONS, "Tag with [needs-dev-input] or remove the implementation choice."),
}


@dataclass
class GateHit:
    rule_id: str
    rule_class: str
    severity: str  # "error" | "warning"
    requirement_id: str
    excerpt: str
    message: str
    suggestion: str


@dataclass
class GateReport:
    gate_version: str = GATE_VERSION
    hits: list = field(default_factory=list)  # list[GateHit as dict]
    errors: int = 0
    warnings: int = 0
    verdict: str = "pass"  # "pass" | "blocking"

    def to_dict(self) -> dict:
        return asdict(self)


def _scan_text(req_id: str, text: str, hits: list[GateHit]) -> None:
    for rule_id, (rule_class, severity, pattern, suggestion) in RULES.items():
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            if rule_id == "G6" and "[needs-dev-input]" in text:
                continue
            start = max(0, m.start() - 40)
            excerpt = ("…" if start else "") + text[start: m.end() + 40].strip()
            hits.append(GateHit(
                rule_id=rule_id, rule_class=rule_class, severity=severity,
                requirement_id=req_id, excerpt=excerpt,
                message=f"{rule_class}: \"{m.group(0)}\"", suggestion=suggestion,
            ))


def run_gate(spec: DraftSpec) -> GateReport:
    hits: list[GateHit] = []

    for req in spec.requirements:
        _scan_text(req.id, req.statement, hits)
        for ac in req.acceptance_criteria:
            _scan_text(req.id, ac, hits)
        if not req.source_claim_ids:
            hits.append(GateHit(
                rule_id="G7", rule_class="missing-provenance", severity="error",
                requirement_id=req.id, excerpt=req.title,
                message="missing-provenance: requirement traces to zero claims",
                suggestion="Link the requirement to wiki claim ids or tag the assumption.",
            ))

    if not spec.out_of_scope:
        hits.append(GateHit(
            rule_id="G8", rule_class="missing-out-of-scope", severity="error",
            requirement_id="(spec)", excerpt=spec.feature_name,
            message="missing-out-of-scope: no explicit scope boundary section",
            suggestion="List what this feature explicitly does NOT change.",
        ))

    report = GateReport()
    report.hits = [asdict(h) for h in hits]
    report.errors = sum(1 for h in hits if h.severity == "error")
    report.warnings = sum(1 for h in hits if h.severity == "warning")
    report.verdict = "blocking" if report.errors else "pass"
    return report
