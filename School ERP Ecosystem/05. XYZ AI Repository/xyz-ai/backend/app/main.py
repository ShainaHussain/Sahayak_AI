from fastapi import FastAPI, Depends

from app.routers import auth as auth_router
from app.routers import attendance as attendance_router
from app.routers import chat as chat_router
from app.auth.dependencies import get_current_user, CurrentUser
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI(title="Sahayak AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router.router)
app.include_router(attendance_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/me")
def whoami(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "role": current_user.role.value,
        "profile_id": current_user.profile_id,
    }