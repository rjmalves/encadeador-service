import pathlib
import os
from app.internal.settings import Settings
from app.utils.log import Log

BASEDIR = pathlib.Path().resolve()
os.environ["APP_INSTALLDIR"] = str(BASEDIR)
os.environ["APP_BASEDIR"] = str(BASEDIR)
Settings.read_environments()
Log.configure_logging(BASEDIR)
