---
description: "Use when creating or modifying Flask route handlers, the REST API v1, the legacy Jinja routes, or session management code for the character creator."
applyTo: "routes/**/*.py"
---

# Flask Route Conventions

The Flask backend exposes two route surfaces:

| Surface | Path prefix | Status | Source |
|---|---|---|---|
| **REST API v1** | `/api/v1/*` | **Primary** — consumed by the React SPA | `routes/api/` |
| **Legacy Jinja UI** | `/legacy/*` | **Quarantined** — kept side-by-side for comparison only | `routes/` (non-`api/`) |
| Test API | `/api/test/*` | Helper endpoints used by integration tests | `routes/test_api.py` |

The React SPA (`frontend/`) is the new UI. Flask serves the built SPA bundle
from `frontend/dist/` at `/` via a catch-all in `app.py`. **All new UI work
goes into the SPA; all new server-side endpoints go into `routes/api/v1`.**
The legacy routes will be removed in a future phase.

## REST API v1 (primary surface)

The API is **stateless** (no Flask sessions) and JSON-only. Every meaningful
request takes the full `choices_made` dict in the body and returns calculated
values from `CharacterBuilder.to_character()`.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness check |
| `GET` | `/api/v1/classes`, `/classes/<name>`, `/classes/<name>/subclasses[/<sub>]` | Class catalog |
| `GET` | `/api/v1/species`, `/species/<name>` | Species catalog |
| `GET` | `/api/v1/backgrounds`, `/backgrounds/<name>` | Background catalog |
| `GET` | `/api/v1/feats`, `/feats/<name>` | Feat catalog |
| `GET` | `/api/v1/spells/<class_name>`, `/spells/definitions/<spell>` | Spell catalog |
| `GET` | `/api/v1/equipment/<kind>` | Equipment catalog |
| `GET` | `/api/v1/reference/<name>` | Misc reference data (fighting styles, etc.) |
| `GET` | `/api/v1/wizard/steps`, `/wizard/dependencies` | Declarative wizard metadata |
| `POST` | `/api/v1/character/build` | **Build full character from `choices_made`** |
| `POST` | `/api/v1/character/validate` | Per-step validation summary |
| `POST` | `/api/v1/character/preview-step` | Preview a single step before commit |
| `POST` | `/api/v1/character/derived` | Stateless derived views (`view=damage_cantrips`, etc.) |

### Pattern

```python
# routes/api/character.py
from flask import Blueprint, jsonify, request
from modules.character_builder import CharacterBuilder

character_bp = Blueprint("character", __name__, url_prefix="/character")
# Mounted under /api/v1 by routes/api/__init__.py

@character_bp.post("/build")
def build_character():
    body = request.get_json(silent=True)
    if not body or "choices_made" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made'"}), 400

    builder = CharacterBuilder()
    builder.apply_choices(body["choices_made"])
    return jsonify({"character": builder.to_character()})
```

### Rules for API v1

1. **Stateless** — never read or write `flask.session`
2. **Pure** — derive everything from the request body via `CharacterBuilder`
3. **No calculations in the route** — call `builder.to_character()` (or a helper from `modules/derived_stats.py`) and return the result as JSON
4. **One blueprint per concern** — `catalog`, `character`, `wizard` register under the parent `api_v1_bp`
5. **JSON in, JSON out** — return `{"character": ...}`, `{"error": "..."}`, etc. Never return HTML

### Stateless helpers

Reusable view-shaping helpers live in `modules/derived_stats.py` and are
shared between the REST API and the legacy summary route. Add new view
projections there, not inline in route handlers.

## Legacy Jinja UI (quarantined)

The legacy session-based UI lives under `routes/` (everything except
`routes/api/`) and is mounted with `url_prefix="/legacy"` in
`routes/__init__.py`. It exists only so users can visually compare the SPA
against the original implementation.

**Do not add new features to the legacy UI.** Bug fixes are acceptable when
they reflect a calculation change in `CharacterBuilder` that should also show
up here.

### Legacy route pattern

```python
@bp.route("/endpoint", methods=["GET", "POST"])
def handler():
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))

    if request.method == "POST":
        builder.apply_choice(key, value)
        save_builder_to_session(builder)

    character = builder.to_character()
    return render_template('template.html', character=character)
```

### Legacy session helpers

```python
from utils.route_helpers import get_builder_from_session, save_builder_to_session
```

- `get_builder_from_session()` → `CharacterBuilder | None`
- `save_builder_to_session(builder)` → serializes to `session['builder_state']`
- Always call `save_builder_to_session(builder)` after any `apply_choice` or setter

### Rules for legacy routes

1. **No calculations in routes** — `builder.to_character()` does all math
2. **No calculations in templates** — Jinja2 only reads pre-calculated values
3. **No direct session access** — use the helpers above
4. **No new endpoints** — extend the API v1 surface instead

## Blueprint registration

All blueprints are registered in `routes/__init__.py` via `register_blueprints(app)`:

- API v1 blueprint registered at `/api/v1`
- Test API blueprint registered at `/api/test`
- Each legacy blueprint registered with `url_prefix=LEGACY_PREFIX` (`/legacy`)

`app.py` then adds a SPA catch-all that serves `frontend/dist/index.html`
for any unmatched non-API, non-legacy, non-static path.
