# WorkProof: Privacy-Focused Work Tracking System

WorkProof is a sophisticated work tracking and monitoring platform designed with a focus on privacy and transparency. It enables organizations to verify work progress through activity tracking, session management, and automated reporting without compromising individual privacy.

---

## 🚀 Project Overview

The system is composed of three main components:
- **Backend API**: A robust FastAPI server with MongoDB (Beanie) integration.
- **Frontend Dashboard**: A modern React-based web interface for admins and employees.
- **Client Agent**: A background laptop application for real-time activity tracking.

---

## ✨ Key Features

### 👤 For Employees
- **Personal Dashboard**: View daily activity summaries and productivity trends.
- **Activity Timeline**: Transparent view of tracked work sessions.
- **Privacy Control**: Explicit consent flow and ability to toggle tracking on/off.
- **Secure Storage**: Local and server-side encryption for sensitive data.

### 👑 For Administrators
- **Team Overview**: Real-time monitoring of team activity and status.
- **Employee Management**: Simplified onboarding and role management.
- **Advanced Reporting**: Generate daily, weekly, and monthly productivity reports.
- **Screenshot Verification**: On-demand visual proof of work for specific sessions.

---

## 🛡️ Security & Privacy

Privacy is the core pillar of WorkProof:
- **Consent-First Architecture**: Tracking only begins after explicit employee agreement.
- **Data Encryption**: All screenshots and sensitive logs are encrypted at rest.
- **Selective Tracking**: System ignores sensitive applications (if configured).
- **Audit Logs**: Transparent tracking of administrative data access.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, Beanie ODM, MongoDB
- **Frontend**: React, Vite, TypeScript, Tailwind CSS, Lucide React
- **Security**: JWT Authentication, Bcrypt Hashing, Fernet Encryption
- **Environment Management**: Conda / Pip / Node.js

---

## 📂 Project Structure

```text
├── backend/                # FastAPI Server & REST APIs
│   ├── app/
│   │   ├── api/            # API Route handlers (Auth, Activity, Admin, Reports)
│   │   ├── models/         # Database models (Beanie/MongoDB)
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic and report generation
│   │   └── main.py         # Backend entry point
│   └── config/             # Environment settings
├── frontend/               # React Web Application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── contexts/       # Auth and state management
│   │   ├── pages/          # Individual page views
│   │   └── App.tsx         # Main application routing
│   └── public/             # Static assets
├── client-agent/           # Desktop tracking application
│   ├── collector/          # Activity and screenshot collection logic
│   ├── sender/             # Data transmission services
│   └── main.py             # Agent entry point
└── storage/                # Data storage: screenshots and reports
```

---

## 🏁 Getting Started

Follow these steps to set up your development environment.

### Prerequisites
- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Node.js](https://nodejs.org/) (LTS version recommended)
- [MongoDB](https://www.mongodb.com/try/download/community) (Local or Atlas instance)

---

### Cloning the project 
```bash 
   git clone https://github.com/AshrayVB30/WorkProof.git
   cd WorkProof
```

### 📦 Backend Setup

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Initialize the Conda environment**
   ```bash
   conda create -n workproof python=3.10
   conda activate workproof
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   - Rename `.env.example` to `.env`
   - Update `MONGODB_URL` with your connection string.

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

---

### 💻 Frontend Setup

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install packages**
   ```bash
   npm install
   ```

3. **Launch the development server**
   ```bash
   npm run dev
   ```

---

## 🔧 Troubleshooting

- **CORS Errors**: Ensure the frontend URL (`localhost:5173`) is listed in the backend `config/settings.py`.
- **Database Connection**: Verify your MongoDB service is running or your Atlas URI is whitelist-accessible.
- **Port Conflicts**: Ensure ports `5000` (Backend) and `5173` (Frontend) are available.

---

## 🔗 Repository Reference
- **GitHub Repository**: [AshrayVB30/WorkProof](https://github.com/AshrayVB30/WorkProof.git)

---

Developed with a focus on efficiency, transparency, and data integrity.