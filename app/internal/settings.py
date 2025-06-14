import os


class Settings:
    clusterId = os.getenv("CLUSTER_ID", "0")
    basedir = os.getenv("APP_BASEDIR", os.curdir)
    installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "80"))
    root_path = os.getenv("ROOT_PATH", "/")
    newave_source = os.getenv("NEWAVE_SOURCE", "FS")
    decomp_source = os.getenv("DECOMP_SOURCE", "FS")
    encoding_script = "app/static/converte_utf8.sh"
    uri_pattern = os.getenv("URI_PATTERN", "BASE62")

    @classmethod
    def read_environments(cls):
        cls.clusterId = os.getenv("CLUSTER_ID", "0")
        cls.basedir = os.getenv("APP_BASEDIR", os.curdir)
        cls.installdir = os.getenv("APP_INSTALLDIR", "/usr/local/bin")
        cls.host = os.getenv("HOST", "localhost")
        cls.port = int(os.getenv("PORT", "80"))
        cls.root_path = os.getenv("ROOT_PATH", "/")
        cls.newave_source = os.getenv("NEWAVE_SOURCE", "FS")
        cls.decomp_source = os.getenv("DECOMP_SOURCE", "FS")
        cls.encoding_script = "app/static/converte_utf8.sh"
        cls.uri_pattern = os.getenv("URI_PATTERN", "BASE62")
