from collections import Counter, defaultdict
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

SINGLE_HAND_FEATURE_COUNT = 63
DUAL_HAND_FEATURE_COUNT = 126
MIN_TOTAL_SAMPLES = 20
MIN_SAMPLES_PER_CLASS = 5


def train_model(db_path, model_path):
    with closing(sqlite3.connect(db_path)) as con:
        rows = con.execute(
            "SELECT label, hindi_label, features FROM samples ORDER BY id"
        ).fetchall()

    if len(rows) < MIN_TOTAL_SAMPLES:
        raise ValueError(
            f"At least {MIN_TOTAL_SAMPLES} samples are required. "
            "Capture multiple samples for each gesture."
        )

    labels = sorted({row[0] for row in rows})
    if len(labels) < 2:
        raise ValueError("Train at least two different gesture classes.")

    counts = Counter(row[0] for row in rows)
    if min(counts.values()) < MIN_SAMPLES_PER_CLASS:
        raise ValueError(
            f"Capture at least {MIN_SAMPLES_PER_CLASS} samples for every "
            "gesture class; 30-100 is recommended."
        )

    translations = defaultdict(set)
    for label, hindi_label, _features in rows:
        translations[label].add(hindi_label)
    inconsistent = [label for label, values in translations.items() if len(values) > 1]
    if inconsistent:
        raise ValueError(
            "Each English label must use one consistent Hindi meaning: "
            + ", ".join(sorted(inconsistent))
        )

    try:
        vectors = []
        for row in rows:
            vector = json.loads(row[2])
            if not isinstance(vector, list):
                raise ValueError
            if len(vector) == SINGLE_HAND_FEATURE_COUNT:
                vectors.append(vector + [0.0] * SINGLE_HAND_FEATURE_COUNT)
            elif len(vector) == DUAL_HAND_FEATURE_COUNT:
                vectors.append(vector)
            else:
                raise ValueError
        X = np.asarray(vectors, dtype=np.float32)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Stored training samples contain invalid feature data.") from error

    if X.shape != (len(rows), DUAL_HAND_FEATURE_COUNT) or not np.isfinite(X).all():
        raise ValueError(
            "Stored training samples must contain 63 or 126 finite values each."
        )

    y = np.asarray([row[0] for row in rows])
    hindi_map = {label: next(iter(values)) for label, values in translations.items()}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    validation_model = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    validation_model.fit(X_train, y_train)
    accuracy = float(accuracy_score(y_test, validation_model.predict(X_test)))

    final_model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    final_model.fit(X, y)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": final_model,
        "hindi_map": hindi_map,
        "labels": labels,
        "samples": len(rows),
        "accuracy": accuracy,
        "feature_count": DUAL_HAND_FEATURE_COUNT,
    }
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=model_path.parent,
            prefix=model_path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
        joblib.dump(bundle, temp_path)
        os.replace(temp_path, model_path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return {
        "accuracy": round(accuracy * 100, 2),
        "samples": len(rows),
        "classes": labels,
        "counts": dict(counts),
        "note": (
            "Holdout accuracy is an estimate on your collected samples, "
            "not a measure of real-world ISL translation."
        ),
    }


def model_status(model_path):
    return {"trained": Path(model_path).is_file()}


def predict_gesture(features, model_path):
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    bundle = joblib.load(path)
    feature_count = int(bundle.get("feature_count", SINGLE_HAND_FEATURE_COUNT))
    values = np.asarray(features, dtype=np.float32)
    if feature_count == DUAL_HAND_FEATURE_COUNT:
        if values.shape == (SINGLE_HAND_FEATURE_COUNT,):
            values = np.concatenate((values, np.zeros(SINGLE_HAND_FEATURE_COUNT, dtype=np.float32)))
        if values.shape != (DUAL_HAND_FEATURE_COUNT,) or not np.isfinite(values).all():
            raise ValueError("Prediction input must contain 126 finite values.")
    else:
        if values.shape == (DUAL_HAND_FEATURE_COUNT,):
            values = values[:SINGLE_HAND_FEATURE_COUNT]
        if values.shape != (SINGLE_HAND_FEATURE_COUNT,) or not np.isfinite(values).all():
            raise ValueError("Prediction input must contain 63 finite values.")
    classifier = bundle["model"]
    probabilities = classifier.predict_proba(values.reshape(1, -1))[0]
    index = int(np.argmax(probabilities))
    label = str(classifier.classes_[index])
    confidence = float(probabilities[index])

    return {
        "label": label,
        "hindi": bundle["hindi_map"].get(label, label),
        "confidence": round(confidence * 100, 1),
        "accepted": confidence >= 0.60,
    }
