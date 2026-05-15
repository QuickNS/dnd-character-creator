<!-- markdownlint-disable-file -->
# Phase 1 — REST API v1

**Status:** COMPLETE — awaiting user approval to proceed to Phase 2.

## Files Created

- `routes/api/__init__.py` — declares `api_v1_bp` Blueprint with `url_prefix="/api/v1"`, registers child blueprints (`catalog_bp`, `character_bp`, `wizard_bp`), exposes `GET /api/v1/health`.
- `routes/api/catalog.py` — read-only catalog endpoints for species, classes, spells, items.
- `routes/api/character.py` — stateless character calculate/preview endpoints (uses `CharacterBuilder`).
- `routes/api/wizard.py` — declarative wizard schema + choice dependency graph for the React frontend to render generically.
- `tests/test_api_v1.py` — 22 pytest tests covering health, catalog (classes/species/backgrounds/feats/spells/equipment), wizard schema/dependencies, character build/validate/preview-step.

## Files Modified

- `app.py` — added try/except `flask-cors` import; CORS enabled for `/api/*` from `http://localhost:5173` only when `FLASK_ENV=development` or `app.debug`.
- `routes/__init__.py` — registers `api_v1_bp` after legacy blueprints.

## Verified

- `python3 -m py_compile routes/api/__init__.py routes/api/catalog.py routes/api/character.py routes/api/wizard.py app.py` → exit 0.
- `python -m pytest tests/test_api_v1.py -v` → **22 passed in 0.29s**.
- Live smoke: `GET /api/v1/health`, `GET /api/v1/wizard/steps`, `GET /api/v1/catalog/classes` all return 200 with expected JSON shape against running Flask dev server.

## Pending / Next Actions

- Present Phase 1 for approval alongside Phase 0.
- Concrete response shapes are now codified in the test file; a separate doc is not required.

## Open Questions (deferred to Phase 2/3)

- Should `POST /api/v1/character/calculate` accept the full wizard choice tree, or accept it incrementally per step? Both `/build` and `/preview-step` exist; the SPA can pick whichever fits the UX.
- Persistence endpoints (`POST /api/v1/character`, `GET /api/v1/character/:id`) remain stubs; deferred to Phase 6.

## Risks (closed)

- `CharacterBuilder` instantiation inside the API works without Flask session state — confirmed by the build/validate/preview tests.
- Catalog spell endpoint already supports `?level=N` filtering; pagination deferred to Phase 3 if needed.