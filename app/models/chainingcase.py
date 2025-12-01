from pydantic import BaseModel, Field, model_validator

from app.models.program import Program


class ChainingCase(BaseModel):
    """
    Case reference for chaining operations.

    Supports two modes:
    1. S3 mode: bucket + execution_hash (preferred)
    2. Legacy mode: id (base62 path) - deprecated

    Examples:
        S3 mode:
        >>> case = ChainingCase(
        ...     program=Program.DECOMP,
        ...     bucket="decomp-bucket",
        ...     execution_hash="abc123def456"
        ... )

        Legacy mode (deprecated):
        >>> case = ChainingCase(
        ...     program=Program.DECOMP,
        ...     id="2cA3xY..."
        ... )
    """

    program: Program = Field(..., description="Program type (DECOMP or NEWAVE)")

    # S3 mode (preferred)
    bucket: str | None = Field(
        None,
        description="S3 bucket containing artifacts",
        examples=["decomp-bucket", "newave-bucket"],
    )
    execution_hash: str | None = Field(
        None,
        description="Unique execution identifier",
        examples=["abc123def456", "xyz789ghi012"],
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    # Legacy mode (deprecated)
    id: str | None = Field(
        None,
        deprecated=True,
        description="Base62-encoded filesystem path (deprecated, use bucket + execution_hash)",
    )

    @property
    def is_s3_mode(self) -> bool:
        """Check if case uses S3 mode."""
        return self.bucket is not None and self.execution_hash is not None

    @property
    def is_legacy_mode(self) -> bool:
        """Check if case uses legacy mode."""
        return self.id is not None and not self.is_s3_mode

    @model_validator(mode="after")
    def validate_mode(self) -> "ChainingCase":
        """Validate that either S3 or legacy mode is specified."""
        if self.is_s3_mode:
            # S3 mode is valid
            return self
        if self.is_legacy_mode:
            # Legacy mode is valid
            return self
        raise ValueError("Must specify either (bucket + execution_hash) or id")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "program": "DECOMP",
                    "bucket": "decomp-bucket",
                    "execution_hash": "abc123def456",
                },
                {
                    "program": "NEWAVE",
                    "id": "2cA3xY7z",
                },
            ]
        }
    }
