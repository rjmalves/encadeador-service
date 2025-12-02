"""Tests for ChainingCase, ChainingRequest, and ChainingResponse models."""

import pytest
from pydantic import ValidationError

from app.models.chainingcase import ChainingCase
from app.models.chainingrequest import ChainingRequest
from app.models.chainingresponse import ChainingResponse
from app.models.chainingresult import ChainingResult
from app.models.chainingvariable import ChainingVariable
from app.models.program import Program


class TestChainingCase:
    """Tests for ChainingCase model."""

    def test_s3_mode_valid(self):
        """Test valid S3 mode with bucket and execution_hash."""
        case = ChainingCase(
            program=Program.DECOMP,
            bucket="decomp-bucket",
            execution_hash="abc123def456",
        )

        assert case.is_s3_mode is True
        assert case.is_legacy_mode is False
        assert case.bucket == "decomp-bucket"
        assert case.execution_hash == "abc123def456"

    def test_legacy_mode_valid(self):
        """Test valid legacy mode with id."""
        case = ChainingCase(
            program=Program.DECOMP,
            id="2cA3xY7z",
        )

        assert case.is_legacy_mode is True
        assert case.is_s3_mode is False
        assert case.id == "2cA3xY7z"

    def test_s3_mode_preferred_over_legacy(self):
        """Test that S3 mode is preferred when both specified."""
        case = ChainingCase(
            program=Program.DECOMP,
            bucket="decomp-bucket",
            execution_hash="abc123",
            id="2cA3xY7z",  # Should be ignored
        )

        assert case.is_s3_mode is True
        assert case.is_legacy_mode is False

    def test_neither_mode_raises_error(self):
        """Test that validation fails when neither mode specified."""
        with pytest.raises(ValidationError, match="Must specify either"):
            ChainingCase(program=Program.DECOMP)

    def test_partial_s3_mode_raises_error(self):
        """Test that validation fails with only bucket."""
        with pytest.raises(ValidationError, match="Must specify either"):
            ChainingCase(
                program=Program.DECOMP,
                bucket="decomp-bucket",  # Missing execution_hash
            )

    def test_partial_s3_mode_execution_hash_only_raises_error(self):
        """Test that validation fails with only execution_hash."""
        with pytest.raises(ValidationError, match="Must specify either"):
            ChainingCase(
                program=Program.DECOMP,
                execution_hash="abc123",  # Missing bucket
            )

    def test_execution_hash_pattern_validation(self):
        """Test that execution_hash must match alphanumeric pattern."""
        # Valid patterns
        ChainingCase(
            program=Program.DECOMP,
            bucket="bucket",
            execution_hash="abc123",
        )
        ChainingCase(
            program=Program.DECOMP,
            bucket="bucket",
            execution_hash="abc-123_XYZ",
        )

        # Invalid pattern
        with pytest.raises(ValidationError, match="pattern"):
            ChainingCase(
                program=Program.DECOMP,
                bucket="bucket",
                execution_hash="abc/123",  # Contains /
            )

    def test_newave_program(self):
        """Test with NEWAVE program."""
        case = ChainingCase(
            program=Program.NEWAVE,
            bucket="newave-bucket",
            execution_hash="xyz789",
        )

        assert case.program == Program.NEWAVE
        assert case.is_s3_mode is True


class TestChainingRequest:
    """Tests for ChainingRequest model."""

    def test_valid_request_s3_mode(self):
        """Test valid request with S3 mode cases."""
        request = ChainingRequest(
            sources=[
                ChainingCase(
                    program=Program.DECOMP,
                    bucket="decomp-bucket",
                    execution_hash="source123",
                )
            ],
            destination=ChainingCase(
                program=Program.DECOMP,
                bucket="decomp-bucket",
                execution_hash="dest456",
            ),
            variable=ChainingVariable.VARM,
        )

        assert len(request.sources) == 1
        assert request.sources[0].is_s3_mode
        assert request.destination.is_s3_mode
        assert request.variable == ChainingVariable.VARM

    def test_valid_request_legacy_mode(self):
        """Test valid request with legacy mode cases."""
        request = ChainingRequest(
            sources=[
                ChainingCase(
                    program=Program.DECOMP,
                    id="source123",
                )
            ],
            destination=ChainingCase(
                program=Program.DECOMP,
                id="dest456",
            ),
            variable=ChainingVariable.TVIAGEM,
        )

        assert request.sources[0].is_legacy_mode
        assert request.destination.is_legacy_mode

    def test_multiple_sources(self):
        """Test request with multiple source cases."""
        request = ChainingRequest(
            sources=[
                ChainingCase(
                    program=Program.DECOMP,
                    bucket="decomp-bucket",
                    execution_hash="source1",
                ),
                ChainingCase(
                    program=Program.DECOMP,
                    bucket="decomp-bucket",
                    execution_hash="source2",
                ),
            ],
            destination=ChainingCase(
                program=Program.DECOMP,
                bucket="decomp-bucket",
                execution_hash="dest",
            ),
            variable=ChainingVariable.GNL,
        )

        assert len(request.sources) == 2

    def test_empty_sources_raises_error(self):
        """Test that empty sources list raises validation error."""
        with pytest.raises(ValidationError, match="at least 1"):
            ChainingRequest(
                sources=[],
                destination=ChainingCase(
                    program=Program.DECOMP,
                    bucket="bucket",
                    execution_hash="dest",
                ),
                variable=ChainingVariable.VARM,
            )


class TestChainingResponse:
    """Tests for ChainingResponse model."""

    def test_response_with_s3_output(self):
        """Test response with S3 output information."""
        response = ChainingResponse(
            result=[
                ChainingResult(id="TUCURUI", value=45.5),
                ChainingResult(id="ITAIPU", value=32.1),
            ],
            output_key="ingest/abc123_encadeado.zip",
            output_bucket="decomp-bucket",
        )

        assert len(response.result) == 2
        assert response.output_key == "ingest/abc123_encadeado.zip"
        assert response.output_bucket == "decomp-bucket"

    def test_response_without_s3_output(self):
        """Test response without S3 output (legacy mode)."""
        response = ChainingResponse(
            result=[ChainingResult(id="TUCURUI", value=45.5)],
        )

        assert response.output_key is None
        assert response.output_bucket is None

    def test_response_serialization(self):
        """Test that response serializes correctly."""
        response = ChainingResponse(
            result=[ChainingResult(id="TUCURUI", value=45.5)],
            output_key="ingest/abc_encadeado.zip",
            output_bucket="decomp-bucket",
        )

        data = response.model_dump()
        assert data["result"] == [{"id": "TUCURUI", "value": 45.5}]
        assert data["output_key"] == "ingest/abc_encadeado.zip"
        assert data["output_bucket"] == "decomp-bucket"
