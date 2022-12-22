from pydantic import BaseModel
from app.models.program import Program


class ChainingCase(BaseModel):
    """
    Class for defining a case that can be chained.
    """

    id: str
    program: Program
