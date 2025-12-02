#!/bin/bash
# Initialize LocalStack S3 buckets for development

echo "Creating S3 buckets..."

awslocal s3 mb s3://decomp-bucket
awslocal s3 mb s3://newave-bucket

echo "S3 buckets created successfully!"

# Optional: Create test data
echo "Creating test artifacts..."

# Create a minimal test deck
mkdir -p /tmp/test-deck
echo "rv0" > /tmp/test-deck/caso.dat
echo "DECOMP test" > /tmp/test-deck/dadger.rv0

cd /tmp/test-deck
zip -r /tmp/deck_processado.zip .

awslocal s3 cp /tmp/deck_processado.zip s3://decomp-bucket/artifacts/test123/entradas/deck_processado.zip

echo "Test data created!"
