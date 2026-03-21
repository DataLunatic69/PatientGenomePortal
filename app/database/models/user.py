from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from uuid imprt UUID, uuid4

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    dna_files: list["DNAFile"] = Relationship(back_populates="user")


from .dna_file import DNAFile
