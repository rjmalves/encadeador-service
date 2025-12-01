from pydantic import BaseModel, Field

from app.models.chainingresult import ChainingResult


class ChainingResponse(BaseModel):
    """
    Response model for chaining operations.

    Contains results and optionally the S3 key of the output artifact.

    Example:
        >>> response = ChainingResponse(
        ...     result=[ChainingResult(...)],
        ...     output_key="ingest/abc123_encadeado.zip",
        ...     output_bucket="decomp-bucket"
        ... )
    """

    result: list[ChainingResult] = Field(
        ...,
        description="List of chaining results",
    )
    output_key: str | None = Field(
        None,
        description="S3 key of the output artifact (for S3 mode)",
        examples=["ingest/abc123_encadeado.zip"],
    )
    output_bucket: str | None = Field(
        None,
        description="S3 bucket of the output artifact (for S3 mode)",
        examples=["decomp-bucket"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result": [
                        {"id": "TUCURUI", "value": 45.5},
                        {"id": "ITAIPU", "value": 32.1},
                    ],
                    "output_key": "ingest/abc123_encadeado.zip",
                    "output_bucket": "decomp-bucket",
                }
            ]
        }
    }
