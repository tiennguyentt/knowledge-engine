# 📐 Knowledge Engine

**Not AI-assisted. Agent-operated.**

An agent-operated **knowledge intelligence system**: raw, contradictory
evidence in — a graded, source-backed, debate-hardened spec out, **ready for
a dev team to build from without follow-up questions**. Role agents do the
work and argue with each other; a human reads the diff and signs off.

The output is not documentation. It is buildable work: requirements with
testable acceptance criteria, every assertion traced to evidence, contradictions
resolved or escalated — graded for dev-readiness before any engineer sees it.

This is a public, fully synthetic rebuild of the PM intelligence system I
operate in my day-to-day product work.

## What it solves

| # | The problem | The answer |
|---|------------|------------|
| 01 | **Stakeholders contradict each other — and specs silently pick a side.** The CEO decides one thing, written policy says another, ops does a third. | A truth hierarchy resolves every contradiction by authority and never hides one: conflicts are surfaced, resolved, and flagged for a human ruling. |
| 02 | **AI writes confident specs with invented facts.** Hallucinated SLAs, imaginary regulatory caveats. | Claims without sources don't exist. Every statement traces to a verbatim quote, a document, code, or a tagged assumption — an adversarial grader hunts the ones that don't. |
| 03 | **Quality depends on who wrote the doc.** Standards live in people's heads. | A deterministic quality gate enforces standards as code — hedge words, vague quantities, missing scope. Models cannot sweet-talk it. |
| 04 | **Documentation ships weeks after the feature.** Docs are downstream cleanup, so they drift. | Documentation is a release gate: nothing advances to sign-off until it passes grading — max three revision rounds, then it blocks loudly. |
| 05 | **The spec says one thing, the code does another.** The gap between intended and actual systems is where incidents live. | Evidence comes from every source — transcripts, documents, code, schemas. Spoken decisions argue by authority; code and data are artifact-state facts no one can out-talk. Gaps become explicit migration requirements. |
| 06 | **Corrections die in chat threads.** The same mistake gets fixed for the tenth time. | Every human edit at sign-off distills into a persistent rule applied on the next run — corrections become institutional memory. |

## Workflow 01 — spec

```
evidence ────▶ 1 source-traced wiki      every claim carries a verbatim quote
             ▶ 2 conflict check          truth hierarchy resolves contradictions, never hides them
             ▶ 3 spec draft              requirements trace to claim ids
             ▶ 4 automated grading       adversarial grader: clarity / sources / testability
             ▶ 5 role debate             Eng Lead × QA × PO argue autonomously; arbiter rules
             ▶ 6 human sign-off          deliberately NOT automated
```

Open the app and you land in the **agent debate** — role agents challenging,
defending, and conceding turn by turn, with a neutral arbiter ruling
accept / amend / reject per requirement.

> All data here is synthetic. No employer or client material is included.

## Run it

```sh
pip install -r requirements.txt
streamlit run app.py
```

- **Replay mode** needs no API key — it plays a recorded run from `data/runs/`.
- **Live mode** runs the real pipeline through any OpenAI-compatible endpoint.
  Default is [OpenRouter](https://openrouter.ai) so cheap models work out of
  the box; paste your key (`sk-or-...`), pick or type any model id, press run,
  and watch the agents argue.

Configuration (optional, env vars): `LLM_BASE_URL`, `KNOWLEDGE_ENGINE_MODEL`.

## Design notes

- **Provider-agnostic by construction.** Structured output is enforced
  client-side: each stage asks for JSON against a pydantic schema, validates,
  and feeds validation errors back for bounded retries (`engine/llm.py`).
  Works on any model, no provider-specific JSON features required.
- **Claims without sources don't exist.** The wiki stage must attach a source
  and verbatim quote to every claim; downstream stages may only reference
  claim ids (`engine/stages.py`).
- **Conflicts resolve up the hierarchy, but never silently.** Decision-maker >
  written policy > ops statement > anecdote. Anything where practice diverges
  from policy is flagged `needs_human_confirmation`.
- **The debate is adversarial by role, not by chance** (`engine/debate.py`).
  Each role has a single job and is told to concede resolved points — the
  arbiter synthesizes amendments from what survives.
- **Run logs are plain JSON** (`data/runs/`), so any run can be replayed,
  downloaded, and diffed without the engine installed.
- **The theme is reusable** (`theme.py` + `.streamlit/config.toml`): the
  design language of [tiennguyentt.github.io](https://tiennguyentt.github.io),
  packaged as a drop-in for every app in this series.

## Roadmap

| # | Milestone | Status |
|---|-----------|--------|
| M1 | Enterprise evidence case (insurance domain), full delivery-team roster (PO, BA, Architect, Eng, QA, DevOps/SRE, Security, Compliance, UX, Scrum Master, Arbiter) phase-gated, deterministic code gate with inline hits, D1–D5 grading with re-grade delta, live-typing work notes, learned-rule vault | next |
| M2 | Public product: FastAPI + Next.js + SSE, shareable run URLs, branded exports (spec PDF/MD + handoff package), cost preflight | committed |
| M3 | Workflow 02: spec → sprint plan | planned |
