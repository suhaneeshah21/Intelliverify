# backend/app/models/user.py

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


# The three roles in the system
class UserRole(str, PyEnum):
    CANDIDATE  = "candidate"
    ADMIN      = "admin"
    SUPERADMIN = "superadmin"


class User(Base):
    __tablename__ = "users"   # this is the actual table name in PostgreSQL

    # Primary key — using UUID instead of 1,2,3... integers
    # UUIDs are better for security (can't guess other user IDs)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Basic info
    full_name    = Column(String(100), nullable=False)
    email        = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(15),  nullable=True)

    # Password is stored hashed — never plain text
    hashed_password = Column(String(255), nullable=False)

    # Role — only allows the three values defined in UserRole above
    role = Column(
        Enum(UserRole),
        default=UserRole.CANDIDATE,
        nullable=False
    )

    # Account state
    is_active   = Column(Boolean, default=True)   # False = banned/deactivated
    is_verified = Column(Boolean, default=False)  # True = email verified (future use)

    # Timestamps — set automatically by the database
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    applications = relationship("Application", back_populates="candidate")


    def __repr__(self):
        return f"<User {self.email} | {self.role}>"