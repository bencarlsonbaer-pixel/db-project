from flask import Flask, redirect, render_template, request, url_for, abort
from dotenv import load_dotenv
import os
import git
import hmac
import hashlib
from db import db_read, db_write
from auth import login_manager, authenticate, register_user
from flask_login import login_user, logout_user, login_required, current_user
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()
W_SECRET = os.getenv("W_SECRET", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

# Init flask app
app = Flask(__name__)
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"
app.secret_key = FLASK_SECRET_KEY

# Init auth
login_manager.init_app(app)
login_manager.login_view = "login"


def is_valid_signature(x_hub_signature: str, data: bytes, private_key: str) -> bool:
    """Validate GitHub webhook signature (X-Hub-Signature)."""
    if not x_hub_signature or "=" not in x_hub_signature:
        return False
    if not private_key:
        return False

    hash_algorithm, github_signature = x_hub_signature.split("=", 1)
    algorithm = getattr(hashlib, hash_algorithm, None)
    if algorithm is None:
        return False

    encoded_key = private_key.encode("latin-1")
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


@app.post("/update_server")
def webhook():
    x_hub_signature = request.headers.get("X-Hub-Signature")

    if not is_valid_signature(x_hub_signature, request.data, W_SECRET):
        logger.warning("Webhook signature invalid")
        return "Unauthorized", 401

    try:
        repo = git.Repo("./mysite")
        origin = repo.remotes.origin
        origin.pull()
        logger.info("Updated PythonAnywhere successfully via webhook")
        return "Updated PythonAnywhere successfully", 200
    except Exception as e:
        logger.exception("Webhook update failed: %s", e)
        return "Update failed", 500


# -----------------------
# Auth routes
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = authenticate(request.form.get("username", ""), request.form.get("password", ""))
        if user:
            login_user(user)
            return redirect(url_for("index"))
        error = "Benutzername oder Passwort ist falsch."

    return render_template(
        "auth.html",
        title="In dein Konto einloggen",
        action=url_for("login"),
        button_label="Einloggen",
        error=error,
        footer_text="Noch kein Konto?",
        footer_link_url=url_for("register"),
        footer_link_label="Registrieren",
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Bitte Benutzername und Passwort ausfüllen."
        else:
            ok = register_user(username, password)
            if ok:
                return redirect(url_for("login"))
            error = "Benutzername existiert bereits."

    return render_template(
        "auth.html",
        title="Neues Konto erstellen",
        action=url_for("register"),
        button_label="Registrieren",
        error=error,
        footer_text="Du hast bereits ein Konto?",
        footer_link_url=url_for("login"),
        footer_link_label="Einloggen",
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# -----------------------
# App routes
# -----------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        todos = db_read(
            "SELECT id, content, due FROM todos WHERE user_id=%s ORDER BY due",
            (current_user.id,),
        )
        return render_template("main_page.html", todos=todos)

    # POST
    content = request.form.get("contents", "").strip()
    due = request.form.get("due_at", None)

    if not content:
        return redirect(url_for("index"))

    db_write(
        "INSERT INTO todos (user_id, content, due) VALUES (%s, %s, %s)",
        (current_user.id, content, due),
    )
    return redirect(url_for("index"))


@app.post("/complete")
@login_required
def complete():
    todo_id = request.form.get("id")
    if not todo_id:
        return redirect(url_for("index"))

    db_write(
        "DELETE FROM todos WHERE user_id=%s AND id=%s",
        (current_user.id, todo_id),
    )
    return redirect(url_for("index"))


# Tutorial-Route: /users (genau wie in der Anleitung)
@app.route("/users", methods=["GET"])
@login_required
def users():
    users = db_read("SELECT username FROM users ORDER BY username", ())
    return render_template("users.html", users=users)


# Optional: Beispiel donors (nur falls ihr wirklich donor-Tabelle nutzt)
@app.route("/donors", methods=["GET"])
@login_required
def donors():
    donors = db_read("SELECT donor_id, name, email, IBAN FROM donor ORDER BY name", ())
    return render_template("donors.html", donors=donors)


if __name__ == "__main__":
    app.run()
