from pydantic import BaseModel
from typing import Optional


class ChainingResult(BaseModel):
    """
    Class for defining a chaining result regarding some
    variable of two cases.
    """

    id: Optional[str]
    value: float
