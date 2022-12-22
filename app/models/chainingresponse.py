from pydantic import BaseModel
from typing import List

from app.models.chainingresult import ChainingResult


class ChainingResponse(BaseModel):
    """
    Class for defining a chaining response regarding two cases.
    """

    result: List[ChainingResult]
