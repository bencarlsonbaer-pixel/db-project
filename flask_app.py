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

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------
# Env
# -----------------------
load_dotenv()
W_SECRET = os.getenv("W_SECRET", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

# -----------------------
# App
# -----------------------
app = Flask(__name__)
app.config["DEBUG"] = FLASK_DEBUG
app.secret_key = FLASK_SECRET_KEY

# -----------------------
# Auth
# -----------------------
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# Helpers: DB schema safety (NO CONSOLE)
# =========================

def donor_has_user_id_column() -> bool:
    """Check if donor.user_id exists. Never crashes the app."""
    try:
        rows = db_read("SHOW COLUMNS FROM donor LIKE 'user_id'", ())
        return bool(rows)
    except Exception:
        logger.exception("Could not check donor.user_id column (donor table missing?)")
        return False


def ensure_donor_user_id_column():
    """
    Try to add donor.user_id if missing.
    If ALTER privileges are missing, it will fail gracefully (no 500).
    """
    try:
        if donor_has_user_id_column():
            return

        logger.info("donor.user_id missing -> trying ALTER TABLE donor ADD COLUMN user_id")
        db_write("ALTER TABLE donor ADD COLUMN user_id INT NULL", ())

        # optional unique (ignore if fails)
        try:
            db_write("ALTER TABLE donor ADD UNIQUE (user_id)", ())
        except Exception:
            pass

        logger.info("donor.user_id added successfully")
    except Exception:
        logger.exception("ensure_donor_user_id_column failed (likely no ALTER privileges)")


def table_exists(table_name: str) -> bool:
    try:
        rows = db_read("SHOW TABLES LIKE %s", (table_name,))
        return bool(rows)
    except Exception:
        return False


# =========================
# GitHub Webhook (AUTO DEPLOY)
# =========================

def is_valid_signature(sig_header: str, data: bytes, secret: str) -> bool:
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
    GitHub webhook:
    - verifies signature
    - auto-stashes local changes to avoid "would be overwritten" error
    - pulls latest code
    """
    try:
        sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Hub-Signature")
        if not is_valid_signature(sig, request.data, W_SECRET):
            return "Unauthorized", 401

        repo_path = os.path.expanduser("~/mysite")
        repo = git.Repo(repo_path)

        # If local changes exist, stash them so pull works
        try:
            if repo.is_dirty(untracked_files=True):
                logger.warning("Repo dirty -> auto-stashing local changes before pull")
                repo.git.stash("push", "-u", "-m", "webhook-autostash")
        except Exception:
            logger.exception("Could not stash changes (continuing)")

        repo.remotes.origin.pull()
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
# App routes (Todos)
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


@app.route("/users", methods=["GET"])
@login_required
def users():
    users = db_read("SELECT username FROM users ORDER BY username", ())
    return render_template("users.html", users=users)


# -----------------------
# Admin Button: link user to donor (NO CONSOLE)
# -----------------------
@app.post("/link_me_as_donor")
@login_required
def link_me_as_donor():
    """
    No-console linking:
    1) tries to create donor.user_id column if missing
    2) if column exists, links current_user to the FIRST donor with user_id IS NULL
    """
    ensure_donor_user_id_column()

    # If we still don't have the column (no ALTER rights), do nothing but never crash
    if not donor_has_user_id_column():
        return redirect(url_for("donors"))

    try:
        db_write(
            """
            UPDATE donor
            SET user_id = %s
            WHERE user_id IS NULL
            LIMIT 1
            """,
            (current_user.id,),
        )
    except Exception:
        logger.exception("link_me_as_donor failed (no donor rows? privileges?)")

    return redirect(url_for("donors"))


# -----------------------
# Donors page (CRASH-SAFE)
# -----------------------
@app.route("/donors", methods=["GET"])
@login_required
def donors():
    """
    This page will NEVER 500:
    - If donor.user_id doesn't exist, we simply skip "my donations" query.
    - If any query fails, we log and show empty sections instead of crashing.
    """
    # We try to add the column, but if it fails, we still render safely.
    ensure_donor_user_id_column()

    # 1) Donor directory
    donors_list = []
    try:
        donors_list = db_read(
            "SELECT donor_id, name, email, IBAN, length_minutes FROM donor ORDER BY name",
            ()
        ) or []
    except Exception:
        logger.exception("Failed loading donor directory")
        donors_list = []

    # 2) Top donors
    top_donors = []
    try:
        top_donors = db_read(
            """
            SELECT d.donor_id,
                   d.name,
                   COALESCE(SUM(dn.amount), 0) AS total_amount,
                   COUNT(dn.donation_id) AS donation_count
            FROM donor d
            LEFT JOIN donation dn ON dn.donor_id = d.donor_id
            GROUP BY d.donor_id, d.name
            ORDER BY total_amount DESC
            LIMIT 10
            """,
            ()
        ) or []
    except Exception:
        logger.exception("Failed loading top_donors")
        top_donors = []

    # 3) Recent donations
    recent_donations = []
    try:
        recent_donations = db_read(
            """
            SELECT dn.date,
                   d.name AS donor_name,
                   dn.amount,
                   COALESCE(c.purpose, '-') AS campaign_purpose
            FROM donation dn
            JOIN donor d ON d.donor_id = dn.donor_id
            LEFT JOIN campaign c ON c.campaign_id = dn.campaign_id
            ORDER BY dn.date DESC, dn.donation_id DESC
            LIMIT 10
            """,
            ()
        ) or []
    except Exception:
        logger.exception("Failed loading recent_donations")
        recent_donations = []

    # 4) My donation path (Use Case 1) — ONLY if donor.user_id exists
    my_spend_path = []
    try:
        if donor_has_user_id_column():
            donor_row = db_read(
                "SELECT donor_id FROM donor WHERE user_id=%s LIMIT 1",
                (current_user.id,)
            ) or []

            if donor_row:
                my_donor_id = donor_row[0]["donor_id"]

                has_dd = table_exists("donation_delivery")
                has_di = table_exists("delivery_item")

                if has_dd:
                    sql = """
                    SELECT
                      dn.donation_id,
                      dn.date,
                      dn.amount,
                      COALESCE(c.purpose, '-') AS campaign_purpose,
                      p.type AS product_type,
                      dd.delivery_id,
                      del.destination,
                      rc.location AS receiver_location,
                      CASE
                        WHEN dd.delivery_id IS NULL THEN 'In Vorbereitung'
                        ELSE 'Geliefert'
                      END AS delivery_status
                    """

                    if has_di:
                        sql += """,
                          di.quantity AS shipped_qty
                        """

                    sql += """
                    FROM donation dn
                    LEFT JOIN campaign c ON c.campaign_id = dn.campaign_id
                    LEFT JOIN products p ON p.product_id = dn.product_id
                    LEFT JOIN donation_delivery dd ON dd.donation_id = dn.donation_id
                    LEFT JOIN delivery del ON del.delivery_id = dd.delivery_id
                    LEFT JOIN receiving_community rc ON rc.community_id = del.community_id
                    """

                    if has_di:
                        sql += """
                        LEFT JOIN delivery_item di
                          ON di.delivery_id = dd.delivery_id
                         AND di.product_id = dn.product_id
                        """

                    sql += """
                    WHERE dn.donor_id = %s
                    ORDER BY dn.date DESC, dn.donation_id DESC
                    """

                    my_spend_path = db_read(sql, (my_donor_id,)) or []
    except Exception:
        logger.exception("Failed loading my_spend_path")
        my_spend_path = []

    return render_template(
        "donors.html",
        donors=donors_list,
        top_donors=top_donors,
        recent_donations=recent_donations,
        my_spend_path=my_spend_path
    )


# -----------------------
# DB Explorer
# -----------------------
@app.route("/dbexplorer", methods=["GET", "POST"])
@login_required
def dbexplorer():
    raw = db_read("SHOW TABLES", ()) or []
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

        selected = [t for t in selected if t in tables]

        for t in selected:
            sql = f"SELECT * FROM `{t}`"
            params = []

            if where_text:
                sql += f" WHERE {where_text}"

            sql += " LIMIT %s"
            params.append(limit)

            try:
                rows = db_read(sql, tuple(params)) or []
            except Exception:
                rows = []
                logger.exception("DB explorer query failed for table=%s", t)

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


if __name__ == "__main__":
    app.run()
