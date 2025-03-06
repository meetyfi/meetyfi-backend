from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.data import Base

class UserType(str, enum.Enum):
    MANAGER = "manager"
    EMPLOYEE = "employee"
    ADMIN = "admin"

class MeetingStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    company_name = Column(String)
    company_size = Column(Integer)
    is_verified = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    phone = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    manager_id = Column(String(8), unique=True, index=True, nullable=False)
    
    otp = Column(String, nullable=True)  
    otp_created_at = Column(DateTime, nullable=True)

    employees = relationship("Employee", back_populates="manager")
    meetings = relationship("Meeting", back_populates="manager")

class ProposedDate(Base):
    __tablename__ = "proposed_dates"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), index=True, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="pending", nullable=False)
    proposed_by_id = Column(Integer, nullable=False)  # ID of the user who proposed this date
    proposed_by_type = Column(String, nullable=False)  # Type of user who proposed (manager/employee)
    is_selected = Column(Boolean, default=False)  # Add this field
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    meeting = relationship("Meeting", back_populates="proposed_dates")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)
    name = Column(String)
    role = Column(String, nullable=True)
    department = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("managers.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    token_expiry = Column(DateTime, nullable=True)

    manager = relationship("Manager", back_populates="employees")
    locations = relationship("Location", back_populates="employee")
    meetings = relationship("EmployeeMeeting", back_populates="employee")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="locations")

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True))
    duration = Column(Integer)  # in minutes
    location = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    rejection_reason = Column(String, nullable=True)
    created_by_id = Column(Integer, nullable=True)
    created_by_type = Column(String)
    manager_id = Column(Integer, ForeignKey("managers.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add client information
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    client_phone = Column(String, nullable=True)

    manager = relationship("Manager", back_populates="meetings")
    employees = relationship("EmployeeMeeting", back_populates="meeting")
    proposed_dates = relationship("ProposedDate", back_populates="meeting", cascade="all, delete-orphan")

class EmployeeMeeting(Base):
    __tablename__ = "employee_meetings"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    meeting_id = Column(Integer, ForeignKey("meetings.id"))

    employee = relationship("Employee", back_populates="meetings")
    meeting = relationship("Meeting", back_populates="employees")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())