"""Entrypoint for the standalone poller process."""

import logging

from worker.scheduler import run

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    run()
