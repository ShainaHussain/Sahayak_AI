# XYZ AI — Human-Like School Assistant

Role-aware AI chat assistant for a school ERP system. Students, Parents, Teachers, and Principals each talk to a persona-matched assistant that understands natural language, calls the right backend tools, and never lets a role see or act on data that isn't theirs.

![Login](docs/screenshots/login.png)


## 📸 Screenshots

| Login | Parent — Attendance Query |
|---|---|
| ![Login](docs/screenshots/login.png) | ![Parent Chat](docs/screenshots/chat-parent.png) |

| Teacher — Marking Attendance | Principal — School Summary |
|---|---|
| ![Teacher Chat](docs/screenshots/chat-teacher.png) | ![Principal Chat](docs/screenshots/chat-principal.png) |

---

## ✅ Verified Working

- Role-based login (JWT) — Student, Parent, Teacher, Principal
- **Student** → asks for own attendance, gets own record only
- **Parent** → asks for child's attendance; if they have multiple children, the assistant asks which one instead of guessing
- **Teacher** → marks and views attendance for students in their own class only
- **Principal** → gets school-wide attendance analytics
- Escalation to teacher/school management — assistant asks for confirmation before submitting, never falsely claims a request went through
- Every permission check happens in backend code (not just the AI's judgment) — tested by trying cross-role access and confirming it's blocked

## ⚠️ Not Yet Complete

- Multi-language responses (language selector exists in UI, backend doesn't translate yet — always replies in English)
- Full voice-driven avatar with lip sync (built a lighter version: persona-colored avatar with a real-time speaking/listening indicator instead)

---

## ⚡ Run It Locally

**Backend**
```powershell
cd backend
uv venv
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```
Create `backend/.env`:
```
GROQ_API_KEY=your-groq-api-key
JWT_SECRET_KEY=any-long-random-string
```
```powershell
uvicorn app.main:app --reload
```

**Frontend**
```powershell
cd frontend
npm install
npm run dev
```

---

## 🔑 Test Accounts

| Username | Password | Role |
|---|---|---|
| `student_rahul` | `password123` | Student |
| `parent_sunita` | `password123` | Parent (2 children: Rahul, Priya) |
| `teacher_verma` | `password123` | Teacher (Class 10-A) |
| `principal_rao` | `password123` | Principal |

---

## 🛠 Tech Stack

`FastAPI` · `LangGraph` · `Groq (Llama 3.3 70B)` · `React` · `JWT` · `Pydantic`

---

## 📁 Structure

```
xyz-ai/
├── backend/
│   └── app/
│       ├── models/     → data schemas + mock school data
│       ├── auth/        → JWT login & role verification
│       ├── mock_api/   → attendance & escalation logic (does the real permission checks)
│       ├── graph/       → LangGraph agent + tools the AI can call
│       └── routers/     → API endpoints
└── frontend/
    └── src/            → React chat UI
```