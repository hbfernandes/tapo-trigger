from __future__ import annotations

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytapo import Tapo

from .const import CONF_CLOUD_PASSWORD, LOGGER


def pytapo_log(msg: str) -> None:
    LOGGER.debug("[pytapo] %s", msg)


def pytapo_warn_log(msg: str) -> None:
    LOGGER.warning("[pytapo] %s", msg)


async def async_is_klap(
    hass: HomeAssistant, host: str, port: int = 80, timeout: float = 2.0
) -> bool:
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"http://{host}:{port}",
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            return "200 OK" in await response.text()
    except (aiohttp.ClientError, TimeoutError):
        return False


def parse_privacy_enabled(status: object) -> bool:
    if isinstance(status, dict):
        if "lens_mask" in status:
            lens_mask = status["lens_mask"].get("lens_mask_info", {})
            enabled = lens_mask.get("enabled")
            if isinstance(enabled, str):
                return enabled.lower() == "on"
            return bool(enabled)

        enabled = status.get("enabled")
        if isinstance(enabled, str):
            return enabled.lower() == "on"
        if enabled is not None:
            return bool(enabled)

    raise RuntimeError(f"Unexpected getPrivacyMode response: {status!r}")


class TapoTriggerClient:
    def __init__(self, hass: HomeAssistant, data: dict):
        host = data["host"]
        username = data.get("username")
        password = data.get("password")
        cloud_password = data.get(CONF_CLOUD_PASSWORD, "")

        password_cloud = ""
        if cloud_password:
            username = "admin"
            password = cloud_password
            password_cloud = cloud_password

        self._controller = Tapo(
            host,
            username,
            password,
            password_cloud,
            "",
            None,
            reuseSession=False,
            printDebugInformation=pytapo_log,
            printWarnInformation=pytapo_warn_log,
            retryStok=False,
            controlPort=data["port"],
            isKLAP=data["klap"],
            hass=hass,
        )

    def get_privacy_raw(self) -> object:
        return self._controller.getPrivacyMode()

    def get_privacy_enabled(self) -> bool:
        return parse_privacy_enabled(self.get_privacy_raw())

    def set_privacy_enabled(self, enabled: bool) -> None:
        result = self._controller.setPrivacyMode(enabled)
        if isinstance(result, dict) and result.get("error_code") not in (None, 0):
            raise RuntimeError(f"Camera rejected privacy change: {result!r}")

    def close(self) -> None:
        close = getattr(self._controller, "close", None)
        if callable(close):
            close()