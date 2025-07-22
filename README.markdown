# StegoNet
StegoNet is a deep learning-based image steganography system for hiding and revealing images using neural networks. This project features a Python backend for processing and a React frontend for user interaction.

## 🗂 Project Structure
```
StegoNet/
│
├── Backend/                   # Python backend with ML models
│   ├── app.py                 # Main backend entry point
│   ├── generate_dummy_models.py
│   ├── models.py              # Model loading and preprocessing
│   ├── hiding_network.pth     # Trained model for hiding image
│   ├── preparation_network.pth
│   ├── reveal_network.pth     # Trained model for revealing image
│   ├── users.db               # Optional user management (SQLite)
│   └── requirements.txt       # Backend dependencies
│
├── Frontend/                  # React frontend
│   ├── public/                # Static files
│   ├── src/                   # React source files
│   ├── package.json           # Frontend package definition
│   ├── package-lock.json
│   └── README.md              # Project documentation
│
└── Testing Images/           # Images for testing hiding/revealing
```

## 🚀 Getting Started

### 1️⃣ Backend Setup
#### Prerequisites
- Python 3.7+
- pip
- PyTorch (for .pth model files)

#### Install Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

#### Run the Backend Server
```bash
python app.py
```
This will start your Flask (or FastAPI) server.

### 2️⃣ Frontend Setup
#### Prerequisites
- Node.js (v14+ recommended)
- npm or yarn

#### Install Frontend Dependencies
```bash
cd Frontend
npm install
```

#### Run the Frontend App
```bash
npm start
```
The React app will run at `http://localhost:3000`.

## 🧠 Features
- Hide a secret image inside a cover image using neural networks.
- Reveal the hidden image from a stego image.
- Frontend to upload and preview images.
- Optional user login support with `users.db`.

## 🧪 Testing
Use the `Testing Images/` folder to try various hide and reveal operations with your trained models.

## 📜 License
MIT License