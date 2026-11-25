# 🤟 Sign Language Recognition System

### AI-Powered Hand Gesture Recognition & Translation System

An AI-powered Sign Language Recognition System developed using Python, Flask, MediaPipe, and Machine Learning. This project recognizes custom hand gestures through a webcam and converts them into Hindi/English text and speech to help improve communication accessibility.

---

## 🚀 Features

- 🤖 AI-Based Hand Gesture Recognition
- 📷 Real-Time Webcam Detection
- 🧠 Machine Learning Model Training
- 🇮🇳 Hindi Language Translation
- 🇬🇧 English Language Translation
- 🔊 Text-to-Speech Output
- 📊 Custom Gesture Dataset Collection
- 🌐 User-Friendly Web Interface
- 💾 SQLite Database Integration

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| MediaPipe | Hand Landmark Detection |
| Scikit-learn | Machine Learning |
| Random Forest | Gesture Classification |
| NumPy | Numerical Processing |
| SQLite | Database |
| HTML | Web Structure |
| CSS | Web Styling |
| JavaScript | Frontend Functionality |
| Web Speech API | Speech Output |

## 📁 Project Structure

```text
SignLanguage-Recognition-System/
│
├── app.py
├── model.py
├── requirements.txt
├── README.md
├── setup_windows.bat
├── start_signvoice.bat
│
├── templates/
│   └── index.html
│
├── static/
│   ├── app.js
│   └── style.css
│
├── artifacts/
│   └── gesture_model.joblib
│
└── .gitignore
```

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR-USERNAME/SignLanguage-Recognition-System.git
```

### 2. Open Project Folder

```bash
cd SignLanguage-Recognition-System
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Run Application

```bash
python app.py
```

### 7. Open in Browser

```text
http://127.0.0.1:5000
```

Allow webcam access when prompted.

## 🧠 How It Works

1. Start the application and enable the webcam.
2. Enter an English gesture label and its Hindi meaning.
3. Capture hand gesture samples using the webcam.
4. Collect samples for at least two gesture classes.
5. Train the Machine Learning model.
6. Show a trained gesture in front of the webcam.
7. The system predicts the gesture.
8. View the recognized text in Hindi or English.
9. Use the speech feature to hear the recognized output.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Application health and dataset status |
| POST | `/api/samples` | Save gesture samples |
| POST | `/api/train` | Train the ML model |
| POST | `/api/predict` | Predict a hand gesture |
| DELETE | `/api/samples` | Delete all samples |
| GET | `/api/model/status` | Check model status |

## 📌 Requirements

- Python 3.10–3.12
- Webcam
- Google Chrome or Microsoft Edge
- Internet connection for initial MediaPipe browser resources
- Windows, Linux, or macOS

## ⚠️ Project Limitations

This is an educational research prototype for recognizing custom static hand gestures. It is not a complete or certified Indian Sign Language translator. Dynamic signs, facial expressions, grammar, and regional variations are not fully supported.

## 🔮 Future Improvements

- Recognition of dynamic hand gestures
- Support for two-hand gestures
- Larger Indian Sign Language dataset
- Improved model accuracy and evaluation
- Mobile application integration
- More regional language support
- Real-time sentence generation

## 🎓 Project Information

**Project Name:** Sign Language Recognition System

**Project Type:** Final Year Project

**Domain:** Artificial Intelligence & Machine Learning

**Programming Language:** Python

## 👨‍💻 Author

**DSR DEVELOPER'S**

---

⭐ If you find this project useful, don't forget to give it a star!

**Contributions and suggestions are welcome.**
