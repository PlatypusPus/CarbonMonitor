"""APScheduler poller that periodically generates and ships readings."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from config import get_settings
from worker.generator import generate_readings
from worker.shipper import ship_readings
from worker.sources import collect_external_readings

logger = logging.getLogger(__name__)


def poll_once() -> int:
    readings = generate_readings() + collect_external_readings()
    ship_readings(readings)
    return len(readings)


def run() -> None:
    minutes = get_settings().poll_interval_minutes
    scheduler = BlockingScheduler()
    scheduler.add_job(poll_once, "interval", minutes=minutes, id="poll_sources")
    logger.info("Poller starting: polling every %d minute(s)", minutes)
    poll_once()
    scheduler.start()
