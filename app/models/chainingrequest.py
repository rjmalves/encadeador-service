from pydantic import BaseModel
from typing import List
from app.models.chainingcase import ChainingCase
from app.models.chainingvariable import ChainingVariable


class ChainingRequest(BaseModel):
    """
    Class for defining a chaining request that relates two cases.
    """

    sources: List[ChainingCase]
    destination: ChainingCase
    variable: ChainingVariable
