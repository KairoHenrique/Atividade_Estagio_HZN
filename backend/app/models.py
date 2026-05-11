import uuid
import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SAEnum
import enum

from app.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING_ANALYSIS = "pending_analysis"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256. Simple but effective for demo."""
    return hashlib.sha256(password.encode()).hexdigest()


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    password_hash = Column(String(64), nullable=True)  # SHA-256 hash
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    status = Column(
        SAEnum(SubmissionStatus),
        default=SubmissionStatus.PENDING_ANALYSIS,
        nullable=False
    )
    ai_analysis = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    verdict = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return self.password_hash == _hash_password(password)

    def __repr__(self):
        return f"<Submission {self.id} - {self.full_name} ({self.status})>"
