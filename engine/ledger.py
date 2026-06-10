"""The Judgment Ledger — learned rules with provenance (v0, fully deterministic).

Rules are born ONLY from explicit human rulings at sign-off, carry full
provenance (which run, which item, who, when), have scope + severity, and can
be revoked. The v0 matcher is keyword/structure-based code (no LLM) so the
cross-run proof — a rule born in Run A visibly firing on Run B — is exact and
honest. Semantic matching can upgrade later without changing the data shape.
"""

import json
import time
from pathlib import Path

from engine.schemas import DraftSpec, LearnedRule

LEDGER_DIR = Path(__file__).resolve().parent.parent / "data" / "ledger"
RULES_FILE = LEDGER_DIR / "rules.json"


def load_rules() -> list[LearnedRule]:
    if not RULES_FILE.exists():
        return []
    raw = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    return [LearnedRule.model_validate(r) for r in raw]


def save_rules(rules: list[LearnedRule]) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(
        json.dumps([r.model_dump() for r in rules], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def next_rule_id(rules: list[LearnedRule]) -> str:
    return f"JR-{len(rules) + 1:03d}"


def propose_rules(run: dict, rulings: list[dict], reviews: list[dict], by: str = "you") -> list[LearnedRule]:
    """Deterministic rule candidates from the human's actual judgment.

    Only non-trivial judgment produces a candidate: a ruling on a
    business-rule conflict, a ruling on a regulatory-grounding decision, or
    an edited/rejected amendment.
    """
    existing = load_rules()
    candidates: list[LearnedRule] = []
    today = time.strftime("%Y-%m-%d")
    run_name = run["meta"].get("kind", "run")

    def _new(title, rule_text, severity, applies_when, born_item) -> LearnedRule:
        return LearnedRule(
            id=next_rule_id(existing + candidates), title=title, rule_text=rule_text,
            severity=severity, enforce_via="preflight", applies_when=applies_when,
            born_run=run_name, born_item=born_item, born_by=by, born_date=today,
        )

    conflicts = run["stages"]["conflicts"]["conflicts"]
    for r in rulings:
        text = r["decision_text"].lower()
        if "policy" in text and any(c["kind"] == "business-rule" for c in conflicts):
            candidates.append(_new(
                "Published policy gates automated behavior",
                "Behavior that contradicts a published, audited policy cannot ship "
                "until the policy is amended — it becomes an explicit launch "
                "precondition with a named owner.",
                "blocking",
                {"target": "draft", "keywords": ["auto-approv", "no human", "without human review", "instantly"],
                 "context": "published policy requires human review"},
                f"ruling on decision #{r['decision_index']} (C1)",
            ))
        if "e-kyc" in text or "regulator" in text or "counsel" in text:
            candidates.append(_new(
                "No regulatory claim without a source",
                "A regulatory obligation may only enter a spec with a verifiable "
                "citation in the evidence corpus; otherwise it carries "
                "[needs-compliance-confirm] and blocks nothing.",
                "blocking",
                {"target": "draft", "keywords": ["circular", "per regulation", "decree", "must be re-verified"],
                 "context": "regulatory claim requires citation"},
                f"ruling on decision #{r['decision_index']}",
            ))
    for rv in reviews:
        if rv["action"] in ("edit", "reject") and rv.get("rationale"):
            candidates.append(_new(
                f"Amendment override #{rv['amendment_index'] + 1}",
                f"Human override recorded: {rv['rationale']}",
                "advisory",
                {"target": "draft", "keywords": [w for w in rv["rationale"].lower().split()[:4] if len(w) > 4]},
                f"{rv['action']} on amendment #{rv['amendment_index'] + 1}",
            ))
    # de-dup by title against existing ledger
    have = {r.title for r in existing}
    return [c for c in candidates if c.title not in have]


def commit_rules(approved: list[LearnedRule]) -> list[LearnedRule]:
    rules = load_rules()
    rules.extend(approved)
    save_rules(rules)
    return rules


def preflight(draft: DraftSpec) -> list[dict]:
    """Run all active rules against a new draft. Pure code, instant."""
    hits: list[dict] = []
    for rule in load_rules():
        if rule.status != "active":
            continue
        aw = rule.applies_when
        if aw.get("target") != "draft":
            continue
        for req in draft.requirements:
            text = (req.statement + " " + " ".join(req.acceptance_criteria)).lower()
            matched = [k for k in aw.get("keywords", []) if k in text]
            if matched:
                hits.append({
                    "rule": rule.model_dump(),
                    "requirement_id": req.id,
                    "matched_keywords": matched,
                    "effect": ("BLOCKED until precondition" if rule.severity == "blocking"
                                else "advisory note attached"),
                })
                break
    return hits
