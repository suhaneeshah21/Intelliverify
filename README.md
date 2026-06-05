# IntelliVerify — Intelligent Document Processing & Verification Platform

> A generalized web platform that automatically extracts and cross-verifies information from educational certificates and application forms using OCR and NLP — demonstrated through DRDO RAC's recruitment verification use case.

---

## What It Does

Organizations receive thousands of applications where candidates manually fill in details (name, marks, GATE score) and upload supporting documents. Verifying that the uploaded documents actually match the form entries is tedious and error-prone when done manually.

IntelliVerify automates this:

1. Candidate fills an application form and uploads supporting documents
2. A background pipeline extracts text from the document using OCR
3. NLP extracts specific fields (name, score, roll number, etc.)
4. The system compares extracted values against what the candidate filled in
5. Mismatches are flagged for admin review with a confidence score
6. Admin approves, rejects, or requests clarification — candidate is notified at every step in real time

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│         Candidate Portal  │  Admin Dashboard  │  Auth           │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP + WebSocket
┌────────────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                            │
│   Auth (JWT)  │  Applications API  │  Admin API  │  WS endpoint │
└───────┬───────────────────────┬──────────────────────────────────┘
        │ SQLAlchemy            │ Celery task dispatch
┌───────▼──────┐        ┌───────▼────────────────────────────────┐
│  PostgreSQL  │        │           Celery Worker                │
│  (all data)  │        │  OpenCV → PaddleOCR → spaCy NER →      │
└──────────────┘        │  Field Comparator → Confidence Scorer  │
                        └───────────────┬────────────────────────┘
┌──────────────┐                        │ Redis pub/sub
│    Redis     │◄───────────────────────┘
│ (broker +    │──── WebSocket broadcast ──► Admin Dashboard
│  pub/sub)    │
└──────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, React Router, Chart.js, plain CSS |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Auth | JWT (PyJWT), bcrypt, role-based access (candidate / admin / superadmin) |
| Async Processing | Celery, Redis |
| ML Pipeline | PaddleOCR, OpenCV, pdfplumber, spaCy NER |
| Real-time | WebSockets, Redis pub/sub |
| Database | PostgreSQL |
| Report Generation | ReportLab (PDF) |
| Containerization | Docker, Docker Compose |

---

## ML Pipeline (5 stages)

```
Document Upload
      │
      ▼
1. Preprocessing (OpenCV)
   - Grayscale conversion
   - Noise reduction
   - Contrast enhancement
   - Deskewing
      │
      ▼
2. Text Extraction (PaddleOCR + pdfplumber)
   - PaddleOCR for scanned images
   - pdfplumber for digital PDFs
      │
      ▼
3. NER Field Extraction (spaCy)
   - Extracts: name, roll number, score, percentage, date, institution
      │
      ▼
4. Field Comparison
   - Compares extracted values against candidate's form entries
   - Handles fuzzy matching for names
      │
      ▼
5. Confidence Scoring
   - Calculates per-field and overall confidence score
   - Low confidence → automatic reupload request
   - High confidence mismatch → flagged for admin review
```

---

## Features

**Candidate Portal**
- Multi-step application form
- Document upload (marksheet, GATE scorecard, degree certificate, caste/EWS certificate)
- Real-time application status tracking
- Reupload flow with specific reasons when OCR confidence is low

**Admin Dashboard**
- Live updates via WebSockets as documents are processed
- Side-by-side document vs form view for mismatch review
- Approve / reject / request clarification actions
- Analytics dashboard (applications by status, documents by verdict, daily submissions)
- PDF report generation per application

**System**
- Role-based access control (candidate, admin, superadmin)
- JWT authentication with refresh tokens
- Async document processing via Celery (non-blocking)
- Full Docker Compose setup

---

## Application Status Flow

```
Submitted → Processing → Verified
                      ↘ Action Required (reupload requested)
                      ↘ Under Review (admin reviewing mismatch)
                      ↘ Rejected
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop

### 1. Clone the repository
```bash
git clone https://github.com/suhaneeshah21/Intelliverify.git
cd Intelliverify
```

### 2. Start PostgreSQL and Redis
```bash
docker-compose up db redis -d
```

### 3. Backend setup
```bash
cd backend
python -m venv formsub
source formsub/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Celery worker (new terminal)
```bash
cd backend
source formsub/Scripts/activate
celery -A worker.celery_app worker --loglevel=info --pool=solo
```

### 5. Frontend setup
```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`

### Environment variables
Create `backend/.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5433/intelliverify
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5173
```

---

## Docker Compose (full stack)

```bash
docker-compose up --build
```

Services: frontend (port 3000), backend (port 8000), PostgreSQL (port 5433), Redis (port 6379), Celery worker

> Note: The ML worker (PaddleOCR + OpenCV + spaCy) requires significant system resources. For production deployment, a minimum of 2GB RAM is recommended for the worker service.

---

## Document Types Supported

| Document | Fields Extracted |
|---|---|
| GATE Scorecard | Name, registration number, score, AIR, paper |
| Marksheet | Name, roll number, percentage, institution |
| Degree Certificate | Name, degree, institution, year |
| Caste / EWS Certificate | Name, category, issuing authority |

---

## Project Structure

```
FormSubmission/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # auth, applications, admin, websocket
│   │   ├── core/                # config, security, websocket manager
│   │   ├── db/                  # database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # business logic, report generation
│   ├── ml/                      # OCR pipeline (preprocessor, OCR engine, NER, comparator, scorer)
│   ├── worker/                  # Celery app and tasks
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # candidate, admin, auth pages
│   │   ├── components/          # shared components
│   │   ├── services/            # API client
│   │   ├── context/             # auth context
│   │   └── styles/              # CSS files
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## What I Learned Building This

- Docker and Docker Compose for multi-service containerization
- PaddleOCR and OpenCV for document preprocessing and text extraction
- spaCy for Named Entity Recognition on extracted text
- WebSockets with Redis pub/sub for live dashboard updates
- Celery for async background task processing
- Role-based JWT authentication across multiple user types
- ReportLab for programmatic PDF generation
- Alembic for database migrations

---

## Deployment

- Frontend: Vercel
- Backend: Runs locally (ML pipeline dependencies — PaddleOCR, OpenCV, spaCy — exceed free-tier cloud resource limits)

---

*Built as a solution to SIH Problem Statement ID 1652 — DRDO RAC document verification*