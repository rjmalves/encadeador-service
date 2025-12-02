from pydantic import BaseModel


class ChainingResult(BaseModel):
    """
    Class for defining a chaining result regarding some
    variable of two cases.
    """

    id: str | None
    value: float
