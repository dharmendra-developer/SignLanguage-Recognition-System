from contextlib import closing
from math import isfinite
from pathlib import Path
import json
import sqlite3
import threading
import webbrowser
from urllib.parse import unquote

from flask import Flask, current_app, g, jsonify, request, render_template
from flask_cors import CORS

from model import model_status, predict_gesture, train_model

BASE = Path(__file__).resolve().parent
DB = BASE / "signvoice.db"
MODEL = BASE / "artifacts" / "gesture_model.joblib"
SINGLE_HAND_FEATURE_COUNT = 63
DUAL_HAND_FEATURE_COUNT = 126
FEATURE_COUNTS = (SINGLE_HAND_FEATURE_COUNT, DUAL_HAND_FEATURE_COUNT)
MAX_SAMPLES_PER_REQUEST = 500
MAX_LABEL_LENGTH = 30
MODEL_LOCK = threading.RLock()


class ApiError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def init_db(database_path):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as con:
        with con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute(
                """CREATE TABLE IF NOT EXISTS samples(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    hindi_label TEXT NOT NULL,
                    features TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_samples_label "
                "ON samples(label)"
            )


def get_db():
    if "db" not in g:
        con = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        con.row_factory = sqlite3.Row
        g.db = con
    return g.db


def close_db(_error=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object.")
    return data


def feature_vector(values):
    if not isinstance(values, list) or len(values) not in FEATURE_COUNTS:
        raise ApiError(
            "Each sample must contain 63 or 126 finite numeric landmark values."
        )

    clean = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ApiError("Landmark values must be finite numbers.")
        try:
            value = float(value)
        except (OverflowError, ValueError):
            raise ApiError("Landmark values must be finite numbers.") from None
        if not isfinite(value):
            raise ApiError("Landmark values must be finite numbers.")
        clean.append(value)
    return clean


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(DB),
        MODEL_PATH=str(MODEL),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if config:
        app.config.update(config)

    CORS(app)
    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify(error=str(error)), error.status_code

    @app.errorhandler(413)
    def handle_large_request(_error):
        return jsonify(error="Request is too large."), 413

    @app.errorhandler(404)
    def handle_not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(error="API endpoint not found."), 404
        return error

    @app.errorhandler(500)
    def handle_internal_error(_error):
        app.logger.exception("Unhandled server error")
        return jsonify(error="An internal server error occurred."), 500

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        with get_db() as con:
            count = con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
            labels = con.execute(
                """SELECT label, hindi_label, COUNT(*) AS n
                   FROM samples
                   GROUP BY label, hindi_label
                   ORDER BY label"""
            ).fetchall()
        return jsonify(
            ok=True,
            samples=count,
            labels=[dict(row) for row in labels],
            model=model_status(app.config["MODEL_PATH"]),
        )

    @app.post("/api/samples")
    def add_samples():
        data = json_object()
        label = data.get("label")
        hindi = data.get("hindi_label")
        samples = data.get("samples")

        if not isinstance(label, str) or not label.strip():
            raise ApiError("English label is required.")
        if not isinstance(hindi, str) or not hindi.strip():
            raise ApiError("Hindi meaning is required.")
        label = label.strip().upper()
        hindi = hindi.strip()
        if len(label) > MAX_LABEL_LENGTH or len(hindi) > MAX_LABEL_LENGTH:
            raise ApiError(f"Labels must be {MAX_LABEL_LENGTH} characters or fewer.")
        if not isinstance(samples, list) or not samples:
            raise ApiError("No landmark samples received.")
        if len(samples) > MAX_SAMPLES_PER_REQUEST:
            raise ApiError(f"A maximum of {MAX_SAMPLES_PER_REQUEST} samples can be sent at once.")

        clean_samples = [feature_vector(row) for row in samples]
        with get_db() as con:
            con.executemany(
                "INSERT INTO samples(label, hindi_label, features) VALUES(?,?,?)",
                [(label, hindi, json.dumps(row)) for row in clean_samples],
            )
        return jsonify(ok=True, saved=len(clean_samples), label=label)

    @app.post("/api/train")
    def train():
        try:
            with MODEL_LOCK:
                result = train_model(app.config["DATABASE"], app.config["MODEL_PATH"])
            return jsonify(ok=True, **result)
        except ValueError as error:
            raise ApiError(str(error)) from error
        except Exception:
            app.logger.exception("Training failed")
            return jsonify(error="Training failed. Check server logs."), 500

    @app.post("/api/predict")
    def predict():
        data = json_object()
        features = feature_vector(data.get("features"))
        try:
            with MODEL_LOCK:
                result = predict_gesture(features, app.config["MODEL_PATH"])
            return jsonify(ok=True, **result)
        except FileNotFoundError:
            raise ApiError("Model is not trained yet. Collect samples and train first.", 409)
        except Exception:
            app.logger.exception("Prediction failed")
            return jsonify(error="Prediction failed. Check server logs."), 500

    @app.delete("/api/samples")
    def delete_samples():
        model_path = Path(app.config["MODEL_PATH"])
        with MODEL_LOCK:
            with get_db() as con:
                result = con.execute("DELETE FROM samples")
                deleted = result.rowcount
            try:
                model_path.unlink(missing_ok=True)
            except OSError:
                app.logger.exception("Could not remove trained model after deleting samples")
                raise ApiError(
                    "Samples were deleted, but the trained model could not be removed.",
                    500,
                )
        return jsonify(ok=True, deleted=deleted)

    @app.delete("/api/samples/<path:label>")
    def delete_label_samples(label):
        label = unquote(label).strip().upper()
        if not label:
            raise ApiError("A gesture label is required.")
        model_path = Path(app.config["MODEL_PATH"])
        with MODEL_LOCK:
            with get_db() as con:
                result = con.execute("DELETE FROM samples WHERE label = ?", (label,))
                deleted = result.rowcount
            if deleted:
                if model_path.is_file():
                    model_path.unlink(missing_ok=True)
        return jsonify(ok=True, deleted=deleted, label=label)

    @app.get("/api/model/status")
    def model_status_route():
        return jsonify(ok=True, **model_status(app.config["MODEL_PATH"]))

    return app


app = create_app()
 

if __name__ == "__main__":
    url = "http://127.0.0.1:5000"
    threading.Timer(1.25, lambda: webbrowser.open_new_tab(url)).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)