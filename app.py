import os
import re

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials
except ImportError:  # pragma: no cover
    firebase_admin = None
    firebase_auth = None
    credentials = None


app = Flask(__name__)
app.secret_key = "secure-notes-dev-key"
BASE_DIR = os.path.dirname(__file__)
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")


def get_user_note_path():
    user = session.get("user") or {}
    email = user.get("email") or "guest"
    safe_name = re.sub(r"[^a-zA-Z0-9@._-]+", "_", email.lower())
    return os.path.join(BASE_DIR, f"notes_{safe_name}.txt")


def initialize_firebase():
    if firebase_admin is None or credentials is None:
        return False
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
        return True
    except Exception:
        return False


def verify_google_token(id_token):
    if not id_token:
        return None

    if firebase_admin is not None and firebase_auth is not None and initialize_firebase():
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            return {
                "uid": decoded.get("uid"),
                "email": decoded.get("email"),
                "name": decoded.get("name") or decoded.get("email") or "User",
            }
        except Exception:
            return None

    # Local development fallback for running without Firebase configured.
    return {
        "uid": "local-dev-user",
        "email": "local@example.com",
        "name": "Local User",
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/session", methods=["POST"])
def api_session():
    payload = request.get_json(silent=True) or {}
    token = payload.get("idToken")

    if not token:
        return jsonify({"error": "Missing idToken"}), 400

    user = verify_google_token(token)
    if not user:
        return jsonify({"error": "Invalid Google token"}), 401

    session["user"] = user
    return jsonify({"status": "ok", "user": user})


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if not session.get("user"):
        return redirect(url_for("home"))

    note = ""
    saved = False

    if request.method == "POST":
        note = request.form.get("note", "")
        path = get_user_note_path()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(note)
        saved = True
    else:
        path = get_user_note_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                note = handle.read()

    user = session["user"]
    return render_template("notes.html", note=note, saved=saved, user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)