"""Constants for the Flexit Roomie integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "flexit_roomie"

CONF_DEVICES = "devices"

DEFAULT_NAME = "Flexit Roomie"
DEFAULT_PORT = 4000

SCAN_INTERVAL = timedelta(seconds=30)

# Index = the value sent with the airflow command.
PRESET_MODES = ["ventilation", "heat_recovery", "air_supply"]
