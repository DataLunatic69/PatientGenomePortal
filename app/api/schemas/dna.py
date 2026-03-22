from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.models.dna_file import DnaFileSource

class DnaFileRead(BaseModel):
    id: UUID
    user_id: UUID
    original_filename: str
    source: DnaFileSource
    storage_path: str
    file_size_bytes: int | None
    uploaded_at: datetime
    parsed_at: datetime | None
    total_variants_parsed: int | None

    model_config = {"from_attributes": True}
