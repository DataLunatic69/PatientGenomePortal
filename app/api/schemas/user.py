from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.models.analysis_job import JobStatus
from app.database.models.dna_file import DnaFileSource
from app.database.models.variant_result import PathogenicityLabel

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserRead(BaseModel):
    id: UUID
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
