"""Index, reset, and test session routes."""

from flask import Blueprint, render_template, session

index_bp = Blueprint("index", __name__)


@index_bp.route("/")
def index():
    """Main landing page for character creation."""
    return render_template("index.html")


@index_bp.route("/reset")
def reset():
    """Reset character creation session."""
    session.clear()
    # Render a page that clears sessionStorage before redirecting
    return render_template("reset.html")


@index_bp.route("/test-session")
def test_session():
    """Test route to check session functionality."""
    if "test_counter" not in session:
        session["test_counter"] = 0
    session["test_counter"] += 1
    session.permanent = True
    session.modified = True
    return f"Session test - Counter: {session['test_counter']}, Session keys: {list(session.keys())}"
