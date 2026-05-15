# D&D 2024 Character Creator

A character creator for D&D 2024 (One D&D), built as a React SPA on top of a Flask + Python calculation engine.

The original Jinja UI is still bundled and served under `/legacy/*` as a side-by-side comparison tool.

## Prerequisites

- Python 3.11+ with `pip`
- Node.js 20+ with `npm`

If you open this repo in the provided dev container, both are already installed.

## Quick Start (production-style: one server)

This is the simplest way to browse the app. Flask serves the SPA bundle from `frontend/dist/` and the legacy UI from `/legacy/*`.

```bash
# 1. Install Python deps
pip install -r requirements.txt

# 2. Build the SPA bundle
cd frontend
npm install
npm run build
cd ..

# 3. Run Flask
python app.py
```

Open:

- **New SPA UI:** <http://localhost:5000/>
- **Legacy Jinja UI:** <http://localhost:5000/legacy/>
- **REST API health check:** <http://localhost:5000/api/v1/health>

If you visit `/` and see a 503 with `"frontend bundle not built"`, run `npm run build` in `frontend/` and reload.

## Development (two servers, hot reload)

For active SPA work you want Vite's hot-module reload. Run Flask and Vite in two terminals.

```bash
# Terminal 1 — Flask API on :5000
export FLASK_ENV=development   # enables CORS for the Vite origin
python app.py

# Terminal 2 — Vite dev server on :5173
cd frontend
npm install        # first time only
npm run dev
```

Open:

- **SPA (dev, hot reload):** <http://localhost:5173/>
- **Legacy Jinja UI:** <http://localhost:5000/legacy/>
- **REST API:** <http://localhost:5000/api/v1/*>

The dev SPA talks to Flask at `http://localhost:5000` via CORS, which is gated by `FLASK_ENV=development`.

## URL map

| Path           | Owner            | Purpose                                                   |
| -------------- | ---------------- | --------------------------------------------------------- |
| `/`            | React SPA        | New character creator UI                                  |
| `/wizard/*`    | React SPA        | Step-by-step builder                                      |
| `/sheet`       | React SPA        | Read-only character sheet                                 |
| `/sheet/pdf`   | React SPA        | Printable PDF-parity sheet (use browser print)            |
| `/legacy/`     | Flask Jinja UI   | Original UI home — kept for comparison                    |
| `/legacy/*`    | Flask Jinja UI   | All legacy flow routes (class, species, background, etc.) |
| `/api/v1/*`    | Flask REST API   | JSON contract consumed by the SPA                         |
| `/static/*`    | Flask static     | Legacy CSS / JS / images                                  |

You can switch between the two UIs at any time:

- The SPA Home shows a **Compare with legacy →** link.
- The legacy navbar shows a **Try the new UI** link and a `LEGACY` badge.

## Tests

```bash
# Python (1800+ tests)
pytest tests/

# Frontend type-check + production build
cd frontend
npm run typecheck
npm run build
```

## Project layout

```text
app.py                 # Flask entrypoint + SPA catch-all
routes/                # Blueprints (legacy under /legacy, REST under /api/v1)
modules/               # CharacterBuilder and calculation engine
data/                  # D&D 2024 game content (JSON)
templates/             # Legacy Jinja templates
frontend/              # React + Vite + TypeScript SPA
  src/                 # SPA source
  dist/                # Built bundle (created by `npm run build`)
tests/                 # pytest suite
```

## More documentation

- [docs/character_builder_guide.md](docs/character_builder_guide.md) — How `CharacterBuilder` works.
- [docs/FEATURE_EFFECTS.md](docs/FEATURE_EFFECTS.md) — The data-driven effects system catalog.
