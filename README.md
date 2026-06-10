# 📐 Knowledge Engine

**Not AI-assisted. Agent-operated.**

An **evidence-backed spec red team** for regulated product work: it audits a
plausible-looking draft spec against transcripts, policy documents, production
code and the database; exposes the defects that cause rework or regulatory
exposure — with verbatim receipts; and returns a **dev-ready corrected diff**
for human approval.

Open the app and you land on the catch: the defects the agent team found in an
approved-looking insurance spec, the corrected diff, the readiness delta
(61 → 92), and the one decision only a human can make. The full machinery —
deterministic code gate, D1–D5 adversarial grading, an 11-role enterprise team
debating through a bounded router, the append-only eval-log — is inspectable
depth behind one click.

The output is not documentation. It is buildable work.

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
evidence ────▶ 1 source-traced wiki     every claim: verbatim quote + locator + claim class
             ▶ 2 conflict check         truth hierarchy; code/DB are artifact-state facts
             ▶ 3 deterministic gate     pure code — models cannot override it
             ▶ 4 D1–D5 grading          adversarial; typed findings P0/P1/P2
             ▶ 5 phase-gated debate     bounded router summons the right specialists
             ▶ 6 corrected diff         amendments + migration requirements, re-graded
             ▶ 7 human sign-off         deliberately NOT automated
```

The default view needs no API key (it replays a recorded run through the real
engine). Live mode runs the whole red team on any OpenAI-compatible endpoint
with your own key, streaming real tokens — agents type as they work.

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
