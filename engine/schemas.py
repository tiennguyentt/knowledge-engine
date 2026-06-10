"""Structured-output schemas for every pipeline stage (v2 — red-team flow).

Pydantic models passed to the LLM layer for client-side validation, plus
pure-data models used by the deterministic gate and the eval-log.
"""

from pydantic import BaseModel, Field


# ---- Evidence layer ---------------------------------------------------------

class SourceRef(BaseModel):
    source_file: str = Field(description="Filename of the evidence source")
    source_type: str = Field(description="'transcript' | 'doc' | 'code' | 'db'")
    locator: str = Field(description="Line/section/table.column locator inside the source")
    speaker: str = Field(description="Speaker role for transcripts; empty otherwise")
    quote: str = Field(description="Short verbatim quote or snippet backing the claim")


class WikiClaim(BaseModel):
    id: str = Field(description="Stable id like W1, W2, ...")
    topic: str
    claim: str = Field(description="One atomic, declarative statement")
    authority: str = Field(
        description="Truth-hierarchy level, e.g. 'CEO decision', 'Written policy', "
        "'Ops statement', 'Anecdote', or 'Artifact state' for code/db facts"
    )
    claim_class: str = Field(
        description="'fact' | 'decision' | 'domain-assumption' | "
        "'regulatory-assumption' | 'recommendation' | 'artifact-state'"
    )
    sources: list[SourceRef]


class Wiki(BaseModel):
    project_summary: str
    claims: list[WikiClaim]


class Conflict(BaseModel):
    id: str
    kind: str = Field(description="'business-rule' (talk vs talk) or 'artifact-state-gap' (talk vs code/db)")
    claim_ids: list[str]
    description: str
    winning_claim_id: str = Field(description="For business-rule: the claim that wins by authority. For artifact-state-gap: the INTENDED behavior claim.")
    winning_authority: str
    resolution: str = Field(description="How the spec should resolve this; artifact gaps become migration requirements")
    needs_human_confirmation: bool


class ConflictReport(BaseModel):
    conflicts: list[Conflict]
    notes: str


# ---- Draft spec (the red-team target; input, not generated) -----------------

class Requirement(BaseModel):
    id: str
    title: str
    statement: str
    acceptance_criteria: list[str]
    source_claim_ids: list[str]


class DraftSpec(BaseModel):
    feature_name: str
    summary: str
    out_of_scope: list[str]
    requirements: list[Requirement]


# ---- Grading (D1-D5) ---------------------------------------------------------

class ChecklistItem(BaseModel):
    dimension: str = Field(description="D1..D5")
    item: str = Field(description="The specific checklist item evaluated")
    result: str = Field(description="'PASS' or 'FAIL'")
    note: str = Field(description="One line: what was inspected / why it failed; empty when PASS")


class Finding(BaseModel):
    id: str = Field(description="F1, F2, ...")
    dimension: str = Field(description="D1..D5")
    priority: str = Field(description="'P0' blocks ship | 'P1' fix before ship | 'P2' defer")
    requirement_id: str
    evidence_ref: str = Field(description="Wiki claim id or source locator this finding rests on; empty if none exists (that absence may BE the finding)")
    claim_class_violation: str = Field(description="e.g. 'regulatory-assumption without source'; empty if n/a")
    description: str
    suggested_fix: str
    assigned_role: str = Field(description="Role key best placed to argue this: po|ba|ux|sa|eng|qa|devops|security|compliance")


class GradeReport(BaseModel):
    checklist: list[ChecklistItem]
    findings: list[Finding]
    scores: dict[str, int] = Field(description="Per-dimension 0-100, keys D1..D5")
    overall_score: int = Field(description="0-100")
    verdict: str = Field(description="'SATISFIED' | 'SATISFIED_WITH_DEFERRED' | 'NEEDS_REVISION'")


# ---- Debate (phase-gated, router-driven) -------------------------------------

class WorkNotes(BaseModel):
    observation: str = Field(description="What this role inspected, max 30 words")
    evidence_refs: list[str] = Field(description="Claim ids / locators consulted")
    risk: str = Field(description="The risk or objection held, max 25 words")
    proposed_change: str = Field(description="Concrete change proposed; empty if none")
    confidence: str = Field(description="'high' | 'medium' | 'low'")
    open_assumption: str = Field(description="Assumption this role is still holding; empty if none")


class Turn(BaseModel):
    work_notes: WorkNotes
    stance: str = Field(description="'challenge' | 'defend' | 'concede'")
    message: str = Field(description="The public utterance, max 110 words, concrete")
    refs: list[str] = Field(description="Finding/requirement/claim ids addressed")


class RouterDecision(BaseModel):
    issue_id: str = Field(description="The open finding id chosen; empty when closing")
    summoned_roles: list[str] = Field(description="1-3 role keys, must be phase-eligible")
    focused_question: str = Field(description="The exact question the summoned roles must answer")
    close_phase: bool
    net_movement: str = Field(description="2-sentence summary of what this phase changed; required when close_phase")


class Amendment(BaseModel):
    requirement_id: str
    finding_ids: list[str]
    before: str = Field(description="The exact text being replaced (statement or AC)")
    after: str = Field(description="The replacement text")
    rationale: str


class AmendmentSet(BaseModel):
    amendments: list[Amendment]
    new_requirements: list[Requirement] = Field(description="e.g. migration requirements born from artifact-state gaps")
    unresolved_human_decisions: list[str] = Field(description="Decisions deliberately left to the human")
    summary: str


class AdvisorItem(BaseModel):
    severity: str = Field(description="'S0' reframe recommended | 'S1' consider | 'S2' polish")
    concern: str
    suggestion: str


class AdvisorReport(BaseModel):
    items: list[AdvisorItem]
    verdict: str = Field(description="'NO_CONCERNS' | 'MINOR_POLISH' | 'REFRAME_RECOMMENDED'")
