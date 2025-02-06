import datetime
import uuid

from pydantic import BaseModel, Field
from numpydantic import NDArray # type: ignore


class School(BaseModel):
    name: str
    location: str | None = None

class Award(BaseModel):
    name: str

class Work(BaseModel):
    title: str
    award_indexes: dict[str, int]

class Metadata(BaseModel):
    submission_time: datetime.datetime
    submission_ip: str
    username: str
    email: str | None
    student_id: str | None
    is_student: bool

class Vote(BaseModel):
    metadata: Metadata
    school: School
    matrix: NDArray
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

