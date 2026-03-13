# 🏠 RenderRoom: Professional AI Interior Design

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI-Gemini%203.1%20%7C%20Imagen%203.0-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**RenderRoom** is a high-fidelity interior design platform that transforms real room photos into professional 4K renders while maintaining absolute architectural integrity.

---

## 🚀 The RoomChic™ Engine

Unlike standard AI filters, RenderRoom utilizes the **RoomChic** methodology to ensure every render is grounded in reality:

1.  **Perspective Triangulation**: Analyzes up to 3 different angles to understand the 3D volume, depth, and blind spots of the room.
2.  **Untouchable Structure**: Walls, windows, doors, and ceiling lines are treated as fixed anchors. The AI is prohibited from altering the core geometry.
3.  **Metric Scaling**: Cross-references standard objects (doors/windows) to ensure all new furniture and decor are perfectly scaled to the room's real dimensions.
4.  **Contextual Memory**: Uses secondary photos as a reference for materials and lighting, ensuring a consistent design even in corners not visible in the primary shot.

---

## 🛠️ Tech Stack

*   **Backend**: Flask (Python 3.14)
*   **AI Vision**: Gemini 3.1 Flash (Ultra-precise architectural analysis)
*   **Image Generation**: Nano Banana 2 / Imagen 3.0 (Surgical Structural Editing)
*   **Database & Auth**: Firebase (Firestore, Storage, Auth)
*   **Payments**: Stripe (Integrated Credit System)
*   **Frontend**: Modern HTML5/CSS3 with TailwindCSS

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/renderroom.git
cd renderroom
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
FIREBASE_STORAGE_BUCKET=your-bucket.firebasestorage.app
GOOGLE_API_KEY=your-gemini-api-key
STRIPE_SECRET_KEY=your-stripe-key
DEBUG_MODE=True  # Set to False for production
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```
Open `http://localhost:8080` in your browser.

---

## 📦 Project Structure

```text
├── app.py              # Main Flask server & AI Logic
├── public/             # Static frontend files (HTML, CSS, JS)
│   ├── index.html      # Landing Page
│   ├── dashboard.html  # User Panel
│   └── wizard.html     # Upload & Style Selection
├── requirements.txt    # Project dependencies
└── DESIGN.md           # UI/UX Design System documentation
```

---

## 🔐 Production Note
To disable the development bypass and enforce real Firebase Authentication, ensure `DEBUG_MODE=False` is set in your production environment variables.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed with ❤️ for the future of Interior Design.
