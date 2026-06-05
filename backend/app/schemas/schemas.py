from pydantic import BaseModel, EmailStr, Field
from typing import Optional,List
from uuid import UUID
from datetime import datetime

from app.models.user import UserRole
import uuid

class UserCreate(BaseModel):
    """
    Shape of data required when registering a new user.
    Frontend sends this in the request body.
    """

    full_name:    str      = Field(..., min_length=2,  max_length=100)
    email:        EmailStr                        # validates email format automatically
    phone_number: Optional[str] = Field(None, max_length=15)
    password:     str      = Field(..., min_length=8,max_length=72)
    role:         UserRole = UserRole.CANDIDATE   # defaults to candidate



class UserOut(BaseModel):
    """
    Shape of user data sent back to frontend.
    Notice it doesn't include password or sensitive info.
    """

    id: UUID
    full_name: str
    email: EmailStr
    phone_number: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class Userupdate(BaseModel):
    """
    Shape for updating a user's profile.
    All fields optional — user updates only what they want to change.
    """
    full_name:    Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=15)




class LoginRequest(BaseModel):
    """
    Shape of data required to log in.
    """
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    What we send back after a successful login.
    Frontend stores this token and sends it with every future request.
    """
    access_token: str
    token_type:   str = "bearer"
    role:         UserRole    # frontend uses this to redirect to correct dashboard
    user:         UserOut     # full user object so frontend doesn't need another API call



class TokenData(BaseModel):
    """
    Shape of data extracted FROM a decoded JWT token.
    Used internally in deps.py when verifying who is making a request.
    """
    user_id: Optional[str] = None
    role:    Optional[str] = None


# backend/schemas/application.py





class DocumentResponse(BaseModel):
    id: str
    document_type: str
    original_filename: str
    status: str
    confidence_score: Optional[float] = None
    reupload_reason: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    # Convert UUID to string on the way out
    @classmethod
    def from_orm_safe(cls, doc):
        return cls(
            id=str(doc.id),
            document_type=doc.document_type.value,
            original_filename=doc.original_filename,
            status=doc.status.value,
            confidence_score=doc.confidence_score,
            reupload_reason=doc.reupload_reason,
            uploaded_at=doc.uploaded_at,
        )


class ApplicationCreate(BaseModel):
    # Personal
    full_name: str
    date_of_birth: str
    phone: str
    category: str
    # Education
    degree: str
    branch: str
    college: str
    graduation_year: str
    percentage: str
    gate_score: Optional[str] = None
    gate_rank: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    candidate_id: str
    full_name: str
    date_of_birth: str
    phone: str
    category: str
    degree: str
    branch: str
    college: str
    graduation_year: str
    percentage: str
    gate_score: Optional[str] = None
    gate_rank: Optional[str] = None
    status: str
    admin_remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    documents: List[DocumentResponse] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_safe(cls, app):
        return cls(
            id=str(app.id),
            candidate_id=str(app.candidate_id),
            full_name=app.full_name,
            date_of_birth=app.date_of_birth,
            phone=app.phone,
            category=app.category,
            degree=app.degree,
            branch=app.branch,
            college=app.college,
            graduation_year=app.graduation_year,
            percentage=app.percentage,
            gate_score=app.gate_score,
            gate_rank=app.gate_rank,
            status=app.status.value,
            admin_remarks=app.admin_remarks,
            created_at=app.created_at,
            documents=[DocumentResponse.from_orm_safe(d) for d in app.documents],
        )