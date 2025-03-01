from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, managers, employees, admin

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

@app.get("/")
async def root():
    return {"message": "Welcome to the Manager-Employee Meeting System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)