# Setup and Deployment Guide

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Git (optional)

## Step-by-Step Setup

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb accountability

# Or using psql:
psql -U postgres
CREATE DATABASE accountability;
\q
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Or on macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux

# Edit .env file with your configuration
# Update at minimum:
# - DATABASE_URL (your PostgreSQL connection string)
# - SECRET_KEY (generate a secure random string)
```

#### Edit `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/accountability
SECRET_KEY=GENERATE_A_SECURE_RANDOM_STRING_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:5175"]
```

**Important:** Generate a secure SECRET_KEY. You can use:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Run migrations:

```bash
# Apply database migrations
alembic upgrade head
```

#### Start backend server:

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# The app will be available at http://localhost:5173 or http://localhost:5175
```

## Testing the System

### 1. Create an Account

1. Open http://localhost:5173 in your browser
2. Click "Create account"
3. Fill in email, username (min 3 chars), and password (min 8 chars)
4. Click "Create account"

### 2. Create a Project

1. After login, you'll see the Dashboard
2. Click "New project"
3. Enter project name and optional description
4. Click "Create"

### 3. Invite Others (Optional)

1. Click on your project
2. Click "Invite"
3. Click "Generate invite"
4. Share the code with others

### 4. Mark Check-ins

1. On the project page, you'll see "Mark done today" button
2. Click it to record your check-in
3. The button will disappear and show your check-in time
4. Other members will see your status update

### 5. View Analytics

1. From the project page, click "View analytics"
2. See streaks, consistency percentages, and total check-ins
3. Members are sorted by consistency

## How It Works

### Daily Reset

- Each project has a timezone and reset hour (default: midnight)
- When the reset hour passes, the previous day is locked
- The background scheduler runs every hour
- Users who didn't check in are marked MISSED
- This happens automatically

### Check-in Rules

- **One check-in per day**: You can only check in once
- **No retroactive check-ins**: You cannot check in for past days
- **No editing**: Once created, check-ins are permanent
- **No deletion**: Records are immutable
- **Silence = missed**: If you don't check in, you're marked MISSED

### Visibility

- All project members see everyone's status
- Check-in times are visible
- Missed days are visible
- Streaks and consistency are calculated and displayed
- No hiding failures

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details with today's status

### Invites
- `POST /invites` - Generate invite code (creator only)
- `POST /invites/accept` - Join project via code

### Check-ins
- `POST /checkins` - Mark done for today

### Analytics
- `GET /analytics/projects/{id}` - Project-wide analytics
- `GET /analytics/users/{user_id}/projects/{project_id}` - User-specific analytics

## Troubleshooting

### CORS errors

If you see CORS errors in the browser console:

1. Check that backend is running on port 8000
2. Check that BACKEND_CORS_ORIGINS in .env includes your frontend URL
3. Restart the backend server after changing .env

### Database connection errors

- Verify PostgreSQL is running
- Check DATABASE_URL in .env is correct
- Ensure database "accountability" exists
- Check username/password are correct

### Migration errors

```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

### Frontend can't connect to backend

- Ensure backend is running on http://localhost:8000
- Check browser console for errors
- Verify .env CORS settings
- Try accessing http://localhost:8000/health directly

## Production Deployment

### Backend

1. Use a production WSGI server (Gunicorn):
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. Set strong SECRET_KEY in .env
3. Use production PostgreSQL database
4. Set up SSL/TLS
5. Configure firewall
6. Use process manager (systemd, supervisor)

### Frontend

```bash
# Build for production
npm run build

# Serve with nginx, apache, or any static file server
# Files will be in dist/
```

### Environment Variables for Production

- Change SECRET_KEY to a strong random value
- Update DATABASE_URL to production database
- Update BACKEND_CORS_ORIGINS to production frontend URL
- Set DEBUG=False equivalent settings

## Architecture Notes

### Backend
- **FastAPI**: Modern async Python web framework
- **SQLAlchemy**: ORM with async support
- **PostgreSQL**: Reliable relational database
- **JWT**: Stateless authentication
- **APScheduler**: Background task scheduling

### Frontend
- **React**: Component-based UI
- **TypeScript**: Type safety
- **TailwindCSS**: Utility-first CSS (minimal, no components)
- **Vite**: Fast build tool

### Design Principles
- Immutability over flexibility
- Transparency over privacy
- Facts over feelings
- Simplicity over features
- Discipline over motivation

## Support

If you encounter issues:

1. Check this guide thoroughly
2. Verify all prerequisites are installed
3. Check terminal output for error messages
4. Ensure database is running and accessible
5. Verify .env configuration

## Security Notes

- JWT tokens expire (access: 30 min, refresh: 7 days)
- Passwords are hashed with bcrypt
- SQL injection protected by SQLAlchemy
- CORS configured for specified origins only
- No sensitive data in client-side storage except tokens
