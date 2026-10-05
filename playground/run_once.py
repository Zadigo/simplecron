from simplecron import base
from simplecron.utils import logger

if __name__ == "__main__":
    base.every(1).hour.do(lambda job: logger.info("Running once"))
    while True:
        base.start_blocking()
