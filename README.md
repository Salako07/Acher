# Accountability System

A real accountability platform for daily commitments. Not a habit tracker, not a motivational app. A system that enforces discipline through immutability and group visibility.

## Philosophy

This system is designed around one principle: **facts, not feelings**.

- Binary outcomes: DONE or MISSED
- Immutable records: No editing, no deletion
- Full transparency: All participants see everything
- Time-locked enforcement: Silence equals failure
- Neutral presentation: The system states reality, it does not coach

## Core Rules

### Accountability Rules

1. **Daily success is binary**: DONE or MISSED
2. **One check-in per user per project per day**: No duplicates
3. **No retroactive check-ins**: You cannot check in for past days
4. **No editing or deleting check-ins**: Records are permanent
5. **Silence = missed**: If you don't check in, you are marked MISSED automatically

### Time Rules

Each project has:
- A fixed timezone
- A daily reset time (default: 00:00)

When the day ends:
- Check-ins are locked
- Missing users are marked MISSED
- No grace periods

### Visibility Rules

All participants see:
- Who checked in
- Who missed
- Timestamps
- Streaks
- Consistency percentages

There is no private mode. Failure is visible.

### Role Rules

**Project Creator:**
- Can invite users
- Can define rules at creation
- Rules are locked after the first check-in

## Technical Stack

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic migrations
- JWT authentication
- APScheduler for auto-marking missed days

### Frontend
- React + TypeScript
- Vite
- TailwindCSS (minimal, austere design)
- React Router

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Update `.env` with your database credentials:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/accountability
SECRET_KEY=your-secret-key-change-this
```

6. Create database:
```bash
createdb accountability
```

7. Run migrations:
```bash
alembic upgrade head
```

8. Start server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Open http://localhost:5173

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details

### Invites
- `POST /invites` - Generate invite code
- `POST /invites/accept` - Join project via code

### Check-ins
- `POST /checkins` - Mark done for today

### Analytics
- `GET /analytics/projects/{id}` - Project analytics
- `GET /analytics/users/{user_id}/projects/{project_id}` - User analytics

## Database Models

### User
- id, email, username, hashed_password, created_at

### Project
- id, name, description, timezone, daily_reset_hour, creator_id, created_at, rules_locked

### ProjectMembership
- id, user_id, project_id, joined_at
- Unique constraint: (user_id, project_id)

### ProjectInvite
- id, project_id, code, created_by, created_at, expires_at, max_uses, current_uses

### DailyCheckin
- id, user_id, project_id, date, status, checked_at, auto_marked
- Unique constraint: (user_id, project_id, date)
- Indexed: (project_id, date), (user_id, project_id)

## Background Tasks

The scheduler runs every hour and:

1. Identifies projects where the day has ended
2. Finds members who didn't check in
3. Creates MISSED records for them
4. Process is idempotent

## Design Decisions

### Why immutable records?
Editing undermines accountability. If you can change history, the system loses credibility.

### Why auto-mark as missed?
Silence is a choice. Not checking in is the same as failing.

### Why full visibility?
Private failure has no consequences. Public failure creates real accountability.

### Why binary outcomes?
Nuance creates excuses. You either did it or you didn't.

### Why minimal UI?
The system should be uncomfortable. Flashy design distracts from the core purpose: tracking whether you did what you said you would.

## Frontend Design Philosophy

The UI follows Apple-caliber minimalism:

- System fonts only
- Neutral color palette
- Typography-driven hierarchy
- Minimal motion
- No decorative elements
- No gamification
- Factual, cold language

The interface should not celebrate success or soften failure. It states facts.

## Development Notes

### Backend structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT utilities
│   ├── scheduler.py         # Background tasks
│   └── routes/
│       ├── auth.py
│       ├── projects.py
│       ├── invites.py
│       ├── checkins.py
│       └── analytics.py
├── alembic/                 # Migrations
├── requirements.txt
└── .env.example
```

### Frontend structure
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Project.tsx
│   │   └── Analytics.tsx
│   ├── types.ts            # TypeScript types
│   ├── api.ts              # API client
│   ├── AuthContext.tsx     # Auth state
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## License

MIT

## Final Note

This system does not optimize for comfort. It optimizes for truth.

If you want to be motivated, use a different app.
If you want to track your progress accurately and be held accountable by your peers, this is the tool.
