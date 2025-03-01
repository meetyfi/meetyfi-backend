from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.data import SessionLocal
from app.routers import auth, managers, employees, admin
from sqlalchemy.orm import Session
from app.utils.password import hash_password
from app.database import Admin

app = FastAPI(
    title="Meetyfi-Backend",
    description="API for managing meetings between managers and employees",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(managers.router, prefix="/api/managers", tags=["Managers"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

def create_default_admin():
    db: Session = SessionLocal()
    default_admin_email = "admin@meetyfi.com"
    default_admin_password = "admin123"

    existing_admin = db.query(Admin).filter(Admin.email == default_admin_email).first()
    if not existing_admin:
        hashed_password = hash_password(default_admin_password)
        new_admin = Admin(email=default_admin_email, password=hashed_password, name="Super Admin")
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"Admin created with email: {default_admin_email} and password: {default_admin_password}")
    else:
        print("Admin already exists.")
    db.close()

@app.on_event("startup")
def startup_event():
    create_default_admin()

@app.get("/")
async def root():
    return {"message": "Welcome to the Manager-Employee Meeting System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)