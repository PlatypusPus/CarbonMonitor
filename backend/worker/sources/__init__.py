"""External data-source clients."""

import logging

from schemas.reading import EmissionReading
from worker.sources import carbon_interface, electricity_maps, openweather

logger = logging.getLogger(__name__)

_CLIENTS = (electricity_maps, carbon_interface, openweather)


def collect_external_readings() -> list[EmissionReading]:
    readings: list[EmissionReading] = []
    for client in _CLIENTS:
        try:
            readings.extend(client.fetch_readings())
        except Exception:
            logger.exception("Unexpected error collecting from %s", client.__name__)
    return readings
