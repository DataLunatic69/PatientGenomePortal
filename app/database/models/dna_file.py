from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class DnaFileSource(StrEnum):
    TWENTYTHREE_AND_ME = "23andme"
    ANCESTRY = "ancestry"
    VCF = "vcf"
    RAW = "raw"


class DnaFile(SQLModel, table=True):
    __tablename__ = "dna_files"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    original_filename: str = Field(max_length=255)
    source: DnaFileSource
    storage_path: str = Field(max_length=512)    # Supabase storage path
    file_size_bytes: int | None = None
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    parsed_at: datetime | None = None
    total_variants_parsed: int | None = None

    # relationships
    user: "User" = Relationship(back_populates="dna_files")
    analysis_jobs: list["AnalysisJob"] = Relationship(back_populates="dna_file")


from app.database.models.user import User  # noqa: E402
from app.database.models.analysis_job import AnalysisJob  # noqa: E402