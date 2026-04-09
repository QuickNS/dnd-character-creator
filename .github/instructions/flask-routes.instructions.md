---
description: "Use when creating or modifying Flask route handlers, API endpoints, or session management code for the character creator web application."
applyTo: "routes/**/*.py"
---

# Flask Route Conventions

## Route Pattern

Every route follows this exact flow:

```python
@bp.route("/endpoint", methods=["GET", "POST"])
def handler():
    # 1. Get builder from session
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    # 2. Apply user choice (POST only)
    if request.method == "POST":
        builder.apply_choice(key, value)
        save_builder_to_session(builder)
    
    # 3. Calculate ALL values via builder
    character = builder.to_character()
    
    # 4. Pass to template — templates ONLY display
    return render_template('template.html', character=character)
```

## Critical Rules

1. **No calculations in routes** — `builder.to_character()` does all math
2. **No calculations in templates** — Jinja2 only reads pre-calculated values
3. **No direct session access** — Use `get_builder_from_session()` and `save_builder_to_session()`
4. **Always save after mutation** — Call `save_builder_to_session(builder)` after any `apply_choice` or setter

## Session Helpers

Import from `utils/route_helpers.py`:

```python
from utils.route_helpers import get_builder_from_session, save_builder_to_session
```

- `get_builder_from_session()` → `CharacterBuilder | None`
- `save_builder_to_session(builder)` → serializes to `session['builder_state']`

## API Endpoints

JSON API routes follow the same builder pattern but return JSON:

```python
@bp.route("/api/endpoint", methods=["POST"])
def api_handler():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    # ... validate data ...
    
    builder = CharacterBuilder()
    builder.apply_choices(data["choices_made"])
    character = builder.to_character()
    
    return jsonify({"success": True, "character_data": character}), 200
```

## Key Stateless API

`POST /api/choices-to-character` — Accepts `{"choices_made": {...}}`, returns full character dict. No session involvement. Use for testing and integration.

## Blueprint Registration

All routes use Flask Blueprints registered in `app.py`:

```python
from routes.character_creation import character_creation_bp
app.register_blueprint(character_creation_bp)
```
