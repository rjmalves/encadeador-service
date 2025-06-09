import pathlib
import os
from app.internal.settings import Settings
from app.utils.log import Log

BASEDIR = pathlib.Path().resolve()
os.environ["APP_INSTALLDIR"] = str(BASEDIR)
os.environ["APP_BASEDIR"] = str(BASEDIR)
os.environ["NEWAVE_SOURCE"] = "TEST"
os.environ["DECOMP_SOURCE"] = "TEST"
Settings.read_environments()
Log.configure_logging(BASEDIR)
