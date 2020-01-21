import os

from configtree import Walker, Updater


walk = Walker(env=os.environ.get("ENV_NAME", "dev"))
update = Updater()
