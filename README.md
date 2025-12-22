# ⚡ PADSALA (v16) | High-Performance Study Protocol

![UI Aesthetic](https://img.shields.io/badge/Aesthetic-Cyber--Zen-blueviolet)
![Tech Stack](https://img.shields.io/badge/Tech-Flask%20%7C%20JS-blue)
![Purpose](https://img.shields.io/badge/Purpose-Deep%20Focus-emerald)

**Padsala** is an advanced academic planning engine designed to synchronize study habits with cognitive biological rhythms. It transforms traditional, static study schedules into a dynamic, immersive **Deep Focus Environment**.

---

## 🚀 Vision
In an era of digital noise, Padsala provides a "Technical Sanctuary" for students. By combining algorithmic schedule generation with a distraction-free learning interface, it allows students to enter a state of "Flow" and master complex subjects with surgical precision.

## ✨ Core Features

### 1. 🧠 Algorithmic Blueprint engine
*   **Context-Aware Planning**: Generates schedules based on specific University, Faculty, and Course metadata.
*   **Temporal Mapping**: Calibrates study intensity based on exam dates and subject-specific difficulty levels.
*   **Biological Synchronization**: Customizes sessions, breaks, and start times to match the user's peak performance windows.

### 2. 🛡️ The Vault (Immersive Focus Mode)
*   **Cyber-Zen UI**: A high-end dark-room interface designed to minimize visual eye-strain and maximize concentration.
*   **YouTube Topic Engine**: Integrated search and embed system to cover specific topics via video without the distractions of the main YouTube platform.
*   **Neural Encoding**: A post-session reflection module that forces active recall of core concepts before closing the timer.
*   **Focus DNA**: Gamified progression system with XP, streaks, and ranks (Student Monk → Superhuman Scholar).

### 🎵 Distraction-Free Media
*   **Integrated Music**: One-click access to Lo-Fi and Binaural focus beats.
*   **Content Embedding**: Paste any YouTube link/topic to study course material directly within the Focus Command Center.

### ❄️ Aesthetic Features
*   **Glassmorphism Design**: Modern, premium UI tokens with backdrop blurs and noise textures.
*   **Snow Particle System**: Atmospheric subtle movements to maintain a calm study environment.
*   **Dynamic Transitions**: Fluid navigation between protocol steps.

---

## 🛠️ Technical Architecture

### **Backend**
*   **Python (Flask)**: Core application logic and API orchestration.
*   **Planner Logic (`planner.py`)**: Distributed algorithms for calculating optimal study loads and task distributions.
*   **Syllabus Engine (`syllabus_db.py`)**: Handles metadata injection and subject retrieval.

### **Frontend**
*   **Vanilla JavaScript**: Optimized, high-performance state management and YouTube API integration.
*   **CSS System**: Custom variable-driven design with interactive animations and responsive grid layouts.
*   **Lucide Icons**: Semantic iconography for a professional finish.

---

## 📦 Installation & Setup

### Prerequisites
*   Python 3.8+
*   Pip (Python Package Manager)

### Installation Steps
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "shedule maker"
   ```

2. **Set up a Virtual Environment** (Recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Metadata**:
   Ensure your syllabus SQLite database or metadata source is present in the project root.

5. **Launch the Engine**:
   ```bash
   python app.py
   ```
6. **Access the Protocol**:
   Open `http://localhost:5000` in your preferred high-performance browser.

---

## 🎮 How to Use
1.  **Initialize**: Click "Initialize Protocol" on the home screen.
2.  **Calibrate**: Select your University, Faculty, and Semester. Choose your core subjects.
3.  **Map**: Define your Exam Dates and assign a "Challenge Level" (Comfortable, Challenging, Intensive) to each.
4.  **Execute**: Compute the Blueprint. Click on any task to enter **The Vault**.
5.  **Focus**: Study with integrated YouTube media or focus music. Complete the "Neural Encoding" reflection once the timer hits zero.

---

## 📑 Project Structure
```text
├── app.py              # Main Flask Entry Point
├── planner.py          # Schedule Generation Algorithms
├── syllabus_db.py      # Metadata Management
├── static/
│   ├── css/style.css   # Premium Cyber-Zen Styling
│   └── js/main.js      # Frontend Logic & YouTube Engine
├── templates/
│   └── index.html      # Immersive UI Template
└── requirements.txt    # Project Dependencies
```

---

## 🛡️ License
Designed for personal academic excellence. Optimized for the next generation of scholars.

**Padsala | Engineered for Excellence.**
