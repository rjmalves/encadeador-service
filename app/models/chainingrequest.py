from pydantic import BaseModel, Field

from app.models.chainingcase import ChainingCase
from app.models.chainingvariable import ChainingVariable


class ChainingRequest(BaseModel):
    """
    Request model for chaining operations.

    Chains variables from source case(s) to destination case.

    Example:
        >>> request = ChainingRequest(
        ...     sources=[ChainingCase(
        ...         program=Program.DECOMP,
        ...         bucket="decomp-bucket",
        ...         execution_hash="source123"
        ...     )],
        ...     destination=ChainingCase(
        ...         program=Program.DECOMP,
        ...         bucket="decomp-bucket",
        ...         execution_hash="dest456"
        ...     ),
        ...     variable=ChainingVariable.VARM
        ... )
    """

    sources: list[ChainingCase] = Field(
        ...,
        description="Source cases to chain from",
        min_length=1,
    )
    destination: ChainingCase = Field(
        ...,
        description="Destination case to chain into",
    )
    variable: ChainingVariable = Field(
        ...,
        description="Variable type to chain",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sources": [
                        {
                            "program": "DECOMP",
                            "bucket": "decomp-bucket",
                            "execution_hash": "abc123",
                        }
                    ],
                    "destination": {
                        "program": "DECOMP",
                        "bucket": "decomp-bucket",
                        "execution_hash": "def456",
                    },
                    "variable": "VARM",
                }
            ]
        }
    }
