# SignVoice AI — Final Year Project

A Flask + MediaPipe + scikit-learn web application prototype for custom static hand-gesture recognition with Hindi/English text and browser speech.

## Requirements
- Python 3.10–3.12 recommended
- Chrome or Edge
- Webcam
- Internet for the MediaPipe browser library and hand landmark model on first load

## Windows setup
### Easiest Windows setup
1. Double-click `setup_windows.bat`.
2. Wait for dependencies to finish installing.
3. The browser will open automatically at `http://127.0.0.1:5000`.
4. For later use, double-click `start_signvoice.bat`.

Keep the SignVoice terminal window open while using the app. Close that window to stop the server.

### Manual setup
1. Extract the ZIP.
2. Open Command Prompt / PowerShell in the `SignVoice_Final_Year` folder.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\activate
   ```
4. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Start Flask:
   ```powershell
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in Chrome or Edge and allow camera access.

## Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## How to train
1. Start the camera.
2. Enter an English class name (e.g. HELLO) and Hindi meaning (e.g. नमस्ते).
3. Hold that pose still and click **Capture 40 samples**.
4. Capture each class from slightly varied positions and lighting. Aim for 100–300 samples per class from multiple recording sessions.
5. Add at least two classes. Click **Train AI model**.
6. Test the trained signs in front of the camera. Select Hindi or English output and click Speak.

## API
- `GET /api/health` — sample counts, labels and whether a trained model exists.
- `POST /api/samples` — add labelled 63-value (one hand) or 126-value (left and right hand) landmark samples. Each value must be finite; labels are limited to 30 characters, and each request accepts up to 500 samples.
- `POST /api/train` — validate the dataset, train a RandomForest classifier and atomically save the model under `artifacts/`.
- `POST /api/predict` — predict one 63-value or 126-value landmark vector. Returns HTTP 409 until a model has been trained.
- `DELETE /api/samples` — delete the complete sample dataset and trained model.

Example sample request:
```json
{
  "label": "HELLO",
  "hindi_label": "नमस्ते",
  "samples": [[0.0, 0.1, 0.2]]
}
```
The example feature row is abbreviated; send exactly 63 finite numbers in every sample. API errors are returned as JSON in the form `{"error": "..."}`.

## Project structure
- `app.py` — Flask routes and SQLite database
- `model.py` — RandomForest training, validation, inference
- `templates/index.html` — web interface
- `static/style.css` — responsive styling
- `static/app.js` — webcam, MediaPipe, capture, prediction, speech
- `artifacts/` — generated model file
- `signvoice.db` — generated SQLite database

## Important research limitations
This is a student research prototype for a **custom static-pose vocabulary**. It is not a complete or certified Indian Sign Language (ISL) translator. ISL includes dynamic motion, two-hand signs, facial expressions, grammar, context and regional variation. The initial model learns only labels and samples that you collect. Its validation accuracy is a random holdout split from that same collected dataset and may be optimistic due to correlated frames. For meaningful evaluation, collect independent signer/session test data, report per-class precision/recall/F1 and confusion matrices, and involve qualified ISL interpreters and Deaf/HoH participants. Do not use this prototype for emergency, legal, medical or other high-stakes communication.

## Next research milestones
1. Record an expert-validated and consented ISL dataset.
2. Implement sequence capture (e.g. 30–60 frames) and a temporal model such as LSTM/1D CNN/Transformer for dynamic signs.
3. Add both-hand and facial-expression features.
4. Add signer-independent evaluation and confusion matrix reporting.
5. Add phrase-level decoding, language selection, accessibility testing and privacy controls.

## Security note
The development server uses Flask debug mode and is intended for local development only. Do not expose it publicly as-is. Add authentication, CSRF protection, upload limits, secure deployment settings and a privacy/consent workflow before production use.
