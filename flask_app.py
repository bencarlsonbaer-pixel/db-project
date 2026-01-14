from flask import Flask, redirect, render_template, request, url_for
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

# Load .env variables (on PythonAnywhere, prefer setting env vars in Web tab)
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

# =========================
# GitHub Webhook (AUTO DEPLOY)
# =========================

WEBHOOK_LOG = os.path.expanduser("~/mysite/webhook.log")


def log_webhook(msg: str):
    """Write webhook debug lines to a file (useful when PA error log doesn't update)."""
    try:
        with open(WEBHOOK_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def is_valid_signature(sig_header: str, data: bytes, secret: str) -> bool:
    """Validate GitHub webhook signature from X-Hub-Signature or X-Hub-Signature-256."""
    if not sig_header or "=" not in sig_header:
        return False
    if not secret:
        return False

    algo, github_sig = sig_header.split("=", 1)
    digestmod = getattr(hashlib, algo, None)
    if digestmod is None:
        return False

    mac = hmac.new(secret.encode("utf-8"), msg=data, digestmod=digestmod)
    return hmac.compare_digest(mac.hexdigest(), github_sig)


@app.post("/update_server")
def webhook():
    """
    GitHub Webhook endpoint:
    - verifies signature
    - pulls latest code into ~/mysite
    """
    try:
        sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Hub-Signature")
        log_webhook(f"--- delivery --- sig_present={bool(sig)} bytes={len(request.data)}")

        if not is_valid_signature(sig, request.data, W_SECRET):
            log_webhook("Unauthorized: signature invalid OR W_SECRET missing")
            return "Unauthorized", 401

        repo_path = os.path.expanduser("~/mysite")
        log_webhook(f"repo_path={repo_path}")

        repo = git.Repo(repo_path)
        repo.remotes.origin.pull()

        log_webhook("Pull OK")
        return "Updated PythonAnywhere successfully", 200

    except Exception as e:
        log_webhook(f"ERROR {type(e).__name__}: {e}")
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


# Tutorial-Route: /users
@app.route("/users", methods=["GET"])
@login_required
def users():
    users = db_read("SELECT username FROM users ORDER BY username", ())
    return render_template("users.html", users=users)


# Donors page (optional)
@app.route("/donors", methods=["GET"])
@login_required
def donors():
    donors = db_read("SELECT donor_id, name, email, IBAN, length_minutes FROM donor ORDER BY name", ())
    return render_template("donors.html", donors=donors)


# -----------------------
# DB Explorer (MySQL)
# -----------------------
@app.route("/dbexplorer", methods=["GET", "POST"])
@login_required
def dbexplorer():
    raw = db_read("SHOW TABLES", ())
    tables = []

    if raw:
        if isinstance(raw[0], dict):
            key = list(raw[0].keys())[0]  # Tables_in_<dbname>
            tables = [r[key] for r in raw]
        else:
            tables = [r[0] for r in raw]

    tables = sorted(tables)

    selected = []
    limit = 50
    where_text = ""
    results = {}

    if request.method == "POST":
        selected = request.form.getlist("tables")
        where_text = (request.form.get("where", "") or "").strip()

        try:
            limit = int(request.form.get("limit", "50"))
        except ValueError:
            limit = 50
        limit = max(1, min(limit, 500))

        # whitelist table names
        selected = [t for t in selected if t in tables]

        for t in selected:
            sql = f"SELECT * FROM `{t}`"
            params = []

            # Optional raw WHERE (advanced; use carefully)
            if where_text:
                sql += f" WHERE {where_text}"

            sql += " LIMIT %s"
            params.append(limit)

            rows = db_read(sql, tuple(params))

            if rows and isinstance(rows[0], dict):
                columns = list(rows[0].keys())
                data_rows = [[r.get(c) for c in columns] for r in rows]
            elif rows:
                columns = [f"col_{i+1}" for i in range(len(rows[0]))]
                data_rows = [list(r) for r in rows]
            else:
                columns, data_rows = [], []

            results[t] = {"columns": columns, "rows": data_rows}

    return render_template(
        "dbexplorer.html",
        tables=tables,
        selected=selected,
        limit=limit,
        where_text=where_text,
        results=results,
    )

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/donate", methods=["GET"])
@login_required
def donate():
    return render_template("donate.html")
    
if __name__ == "__main__":
    app.run()
