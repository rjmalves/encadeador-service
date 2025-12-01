import os


class Settings:
    # Application settings
    clusterId = os.getenv("CLUSTER_ID", "0")
    basedir = os.getenv("APP_BASEDIR", os.curdir)
    installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "80"))
    root_path = os.getenv("ROOT_PATH", "/")
    newave_source = os.getenv("NEWAVE_SOURCE", "FS")
    decomp_source = os.getenv("DECOMP_SOURCE", "FS")
    uri_pattern = os.getenv("URI_PATTERN", "BASE62")

    # S3 Configuration
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
    default_decomp_bucket = os.getenv("DEFAULT_DECOMP_BUCKET", "decomp-bucket")
    default_newave_bucket = os.getenv("DEFAULT_NEWAVE_BUCKET", "newave-bucket")

    # Processing
    temp_dir = os.getenv("TEMP_DIR", "/tmp/encadeador")
    zip_compression_level = int(os.getenv("ZIP_COMPRESSION_LEVEL", "6"))
    max_temp_dir_age_hours = int(os.getenv("MAX_TEMP_DIR_AGE_HOURS", "24"))

    @classmethod
    def read_environments(cls):
        # Application settings
        cls.clusterId = os.getenv("CLUSTER_ID", "0")
        cls.basedir = os.getenv("APP_BASEDIR", os.curdir)
        cls.installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
        cls.host = os.getenv("HOST", "localhost")
        cls.port = int(os.getenv("PORT", "80"))
        cls.root_path = os.getenv("ROOT_PATH", "/")
        cls.newave_source = os.getenv("NEWAVE_SOURCE", "FS")
        cls.decomp_source = os.getenv("DECOMP_SOURCE", "FS")
        cls.uri_pattern = os.getenv("URI_PATTERN", "BASE62")

        # S3 Configuration
        cls.aws_region = os.getenv("AWS_REGION", "us-east-1")
        cls.s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
        cls.default_decomp_bucket = os.getenv("DEFAULT_DECOMP_BUCKET", "decomp-bucket")
        cls.default_newave_bucket = os.getenv("DEFAULT_NEWAVE_BUCKET", "newave-bucket")

        # Processing
        cls.temp_dir = os.getenv("TEMP_DIR", "/tmp/encadeador")
        cls.zip_compression_level = int(os.getenv("ZIP_COMPRESSION_LEVEL", "6"))
        cls.max_temp_dir_age_hours = int(os.getenv("MAX_TEMP_DIR_AGE_HOURS", "24"))
