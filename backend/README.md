# WorkProof Backend

FastAPI-based backend for the WorkProof work verification platform.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access control (Admin/Employee)
- **Activity Tracking**: Record and analyze employee work activities
- **Work Sessions**: Automatically detect and group activities into work sessions
- **Daily Reports**: Generate comprehensive daily work summaries
- **Export Reports**: PDF and Excel export functionality
- **Privacy-Focused**: Secure data handling with encryption

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Create PostgreSQL database:
```sql
CREATE DATABASE workproof_db;
CREATE USER workproof WITH PASSWORD 'workproof123';
GRANT ALL PRIVILEGES ON DATABASE workproof_db TO workproof;
```

4. Run the application:
```bash
python -m backend.app.main
```

The API will be available at `http://localhost:5000`

API documentation: `http://localhost:5000/api/docs`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Activity
- `POST /api/activity/submit` - Submit single activity
- `POST /api/activity/batch` - Submit multiple activities
- `POST /api/activity/screenshot` - Upload screenshot
- `GET /api/activity/user/{user_id}` - Get user activities
- `GET /api/activity/stats/{user_id}` - Get activity statistics
- `GET /api/activity/live` - Get real-time activity (admin only)

### Reports
- `GET /api/reports/daily/{user_id}` - Get daily report
- `GET /api/reports/range/{user_id}` - Get reports for date range
- `GET /api/reports/export/pdf/{user_id}` - Export as PDF
- `GET /api/reports/export/excel/{user_id}` - Export as Excel
- `GET /api/reports/team` - Team overview (admin only)

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   ├── dependencies.py   # FastAPI dependencies
│   └── main.py           # Application entry point
├── config/
│   └── settings.py       # Configuration
└── requirements.txt      # Python dependencies
```

## Development

Run with auto-reload:
```bash
uvicorn backend.app.main:app --reload --port 5000
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Role-based access control
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
