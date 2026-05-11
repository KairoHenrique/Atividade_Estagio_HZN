from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SubmissionCreate(BaseModel):
    full_name: str
    email: str
    phone: str


class SubmissionResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    original_filename: str
    status: str
    ai_analysis: Optional[str] = None
    score: Optional[int] = None
    verdict: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    original_filename: str
    status: str
    score: Optional[int] = None
    verdict: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VerdictRequest(BaseModel):
    action: str  # "approve" or "reject"


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str
    submission_id: Optional[str] = None
