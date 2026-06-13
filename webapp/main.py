"""Knowledge Engine — mobile app (FastHTML / pure Python).

A real app shell (top bar + scrolling content + fixed bottom action bar), not a
responsive desktop sidebar. Renders the engine's recorded run-JSON; being a
Python server (Starlette/uvicorn under FastHTML) it imports the engine directly,
so live runs can be wired server-side later without leaving Python.

Run locally:  uvicorn webapp.main:app --reload --port 8600
Deploy:       any Python host (Railway / Render / HF Spaces) with start command
              uvicorn webapp.main:app --host 0.0.0.0 --port $PORT
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # so `import build` works under uvicorn

from fasthtml.common import FastHTML
from starlette.responses import HTMLResponse, PlainTextResponse

from build import RUN_PATH, TEMPLATE, add_eval, build_view_model  # noqa: E402

app = FastHTML()


def _render() -> str:
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    vm = build_view_model(run)
    add_eval(vm, run)
    return TEMPLATE.replace("__DATA__", json.dumps(vm, ensure_ascii=False))


_HTML = _render()


@app.get("/")
def home():
    return HTMLResponse(_HTML)


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")
