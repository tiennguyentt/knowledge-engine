"""Standards alignment (PM-audit P1) — INCOSE & EARS mapping, pure code.

Maps what the engine already enforces onto two recognized requirements-
engineering vocabularies, so an enterprise reviewer can read the gate and
rubric in terms they audit against:

- INCOSE Guide for Writing Requirements: quality characteristics
  (Unambiguous, Verifiable, Complete, Correct, Appropriate, Necessary,
  Traceable, Consistent). We map at the characteristic level only — no
  clause numbers are cited, and the mapping is ours, not a certification.
- EARS (Easy Approach to Requirements Syntax): requirement-shape patterns
  (Ubiquitous, Event-driven, State-driven, Unwanted-behaviour, Optional).
  Classification is a keyword heuristic and labeled as such.

No model calls; runs identically on scripted and live runs.
"""

import re

GATE_TO_INCOSE = {
    "G1": ("Unambiguous", "Hedge words (should/may/might) leave behavior negotiable."),
    "G2": ("Verifiable", "Vague quantities (promptly, quickly) cannot be tested against."),
    "G3": ("Unambiguous", "Passive/future voice hides the acting system or actor."),
    "G4": ("Appropriate", "Catch-all phrases (handle appropriately) defer the real decision."),
    "G5": ("Complete", "An open question inside a requirement is an unfinished decision."),
    "G6": ("Appropriate (solution-free)", "Untagged implementation choices prescribe design inside requirements."),
    "G7": ("Necessary & Traceable", "A requirement tracing to zero source claims has no demonstrated origin."),
    "G8": ("Complete (set)", "A spec without explicit out-of-scope leaves the boundary undefined."),
}

DIMENSION_TO_INCOSE = {
    "D1": ("Complete & Consistent (set)", "Every source direction addressed; contradictions surfaced, never silently resolved."),
    "D2": ("Complete", "Edge cases and failure paths beyond what sources literally said."),
    "D3": ("Correct & Traceable", "Every domain fact traces to a claim id; invented facts are P0."),
    "D4": ("Appropriate scope", "Explicit out-of-scope; no unplanned dependencies smuggled in."),
    "D5": ("Verifiable", "Testable acceptance criteria, explicit numbers, active voice."),
}

EARS_PATTERNS = [
    ("Unwanted behaviour (If-Then)", re.compile(r"\bif\b.+\bthen\b", re.I | re.S)),
    ("Event-driven (When)", re.compile(r"\bwhen\b", re.I)),
    ("State-driven (While)", re.compile(r"\b(while|during|as long as)\b", re.I)),
    ("Optional (Where)", re.compile(r"\bwhere\b", re.I)),
]

_GWT = re.compile(r"\bgiven\b.+\bwhen\b.+\bthen\b", re.I | re.S)


def classify_ears(statement: str) -> str:
    """Heuristic EARS pattern for a requirement statement."""
    for label, rx in EARS_PATTERNS:
        if rx.search(statement):
            return label
    return "Ubiquitous"


def is_gwt(ac: str) -> bool:
    """True if an acceptance criterion is in Given-When-Then form."""
    return bool(_GWT.search(ac))


def alignment_report(run: dict) -> dict:
    """Per-requirement EARS classification + GWT coverage of the corrected spec."""
    spec = run["stages"]["corrected_spec"]
    rows = []
    for r in spec["requirements"]:
        acs = r.get("acceptance_criteria", [])
        gwt = sum(1 for ac in acs if is_gwt(ac))
        rows.append({
            "id": r["id"],
            "title": r["title"],
            "ears": classify_ears(r["statement"]),
            "acs_total": len(acs),
            "acs_gwt": gwt,
        })
    total = sum(r["acs_total"] for r in rows)
    gwt = sum(r["acs_gwt"] for r in rows)
    return {"requirements": rows, "acs_total": total, "acs_gwt": gwt}
