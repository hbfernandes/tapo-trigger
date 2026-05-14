#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from pytapo import Tapo


def is_klap(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        response = requests.get(f"http://{host}:{port}", timeout=timeout)
    except requests.RequestException:
        return False
    return "200 OK" in response.text


def build_controller(args: argparse.Namespace) -> Tapo:
    username = args.username
    password = args.password
    password_cloud = ""

    if args.cloud_password:
        username = "admin"
        password = args.cloud_password
        password_cloud = args.cloud_password

    return Tapo(
        args.host,
        username,
        password,
        password_cloud,
        "",
        None,
        reuseSession=False,
        retryStok=False,
        controlPort=args.port,
        isKLAP=args.klap,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enable, disable, toggle, or read Tapo camera privacy mode."
    )
    parser.add_argument("host", help="Camera IP or hostname")
    parser.add_argument(
        "action",
        choices=["on", "off", "toggle", "status", "test"],
        help="Privacy-mode action to perform",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("TAPO_USERNAME"),
        help="Tapo third-party username or TAPO_USERNAME env var",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("TAPO_PASSWORD"),
        help="Tapo third-party password or TAPO_PASSWORD env var",
    )
    parser.add_argument(
        "--cloud-password",
        default=os.getenv("TAPO_CLOUD_PASSWORD"),
        help="Cloud password auth shortcut used by the integration for some cameras",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="Camera control port, usually 443 or 80 for KLAP devices",
    )
    parser.add_argument(
        "--klap",
        action="store_true",
        help="Force KLAP mode instead of auto-detecting it from port 80",
    )
    args = parser.parse_args()

    if not args.cloud_password and (not args.username or not args.password):
        parser.error("Provide either --cloud-password or both --username and --password")

    if not args.klap and args.port == 443 and is_klap(args.host, 80):
        args.klap = True
        args.port = 80
    elif not args.klap and args.port == 80:
        args.klap = True
    elif not args.klap and args.port != 443:
        args.klap = is_klap(args.host, args.port)

    return args


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


def get_privacy_enabled(controller: Tapo) -> bool:
    return parse_privacy_enabled(controller.getPrivacyMode())


def set_privacy_enabled(controller: Tapo, enabled: bool) -> None:
    result = controller.setPrivacyMode(enabled)
    if isinstance(result, dict) and result.get("error_code") not in (None, 0):
        raise RuntimeError(f"Camera rejected privacy change: {result!r}")


def main() -> int:
    args = parse_args()

    try:
        controller = build_controller(args)
        raw_status = controller.getPrivacyMode()

        if args.action == "test":
            print(json.dumps(raw_status, indent=2, sort_keys=True, default=str))
            return 0

        current = parse_privacy_enabled(raw_status)

        if args.action == "status":
            print("on" if current else "off")
            return 0

        desired = current
        if args.action == "on":
            desired = True
        elif args.action == "off":
            desired = False
        elif args.action == "toggle":
            desired = not current

        if desired != current:
            set_privacy_enabled(controller, desired)

        updated = get_privacy_enabled(controller)
        print("on" if updated else "off")
        return 0
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())