from simplecron import base
from simplecron.utils import logger

if __name__ == "__main__":
    base.once(lambda: logger.info("Running once"))
