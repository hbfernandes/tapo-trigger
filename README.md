# tapo-trigger

This repository contains two related but separate ways to control Tapo camera privacy mode:

1. A Home Assistant custom integration for HACS/manual installation.
2. A standalone Python CLI script at the repository root.

They both use `pytapo`, but they are meant for different environments.

## Repository layout

### Home Assistant integration

The Home Assistant integration lives under `custom_components/tapo_trigger`.

What it provides:

- a native Home Assistant config flow
- one coordinator-backed switch entity for camera privacy mode
- configurable polling interval via integration options
- auto-detection of KLAP on port 80 when using the default port 443
- built-in dependency installation through the integration manifest

Current baseline:

- Home Assistant: `2026.5.1`
- `pytapo`: `3.4.13`

### Root CLI script

The standalone script lives at the repository root as `privacy_mode.py`.

What it provides:

- `status`, `on`, `off`, and `toggle` actions
- `test` action to print the raw `getPrivacyMode()` payload
- support for username/password auth or cloud-password auth
- optional KLAP forcing on port 80
- environment-variable support for credentials

This is useful for local testing, debugging firmware behavior, or calling the camera outside Home Assistant.

## Home Assistant integration

### Install with HACS

1. Add this repository as a custom HACS repository.
2. Choose category `Integration`.
3. Install `Tapo Trigger`.
4. Restart Home Assistant.
5. Add `Tapo Trigger` from `Settings -> Devices & services`.

The integration installs its Python dependency from [custom_components/tapo_trigger/manifest.json](custom_components/tapo_trigger/manifest.json), so you do not need a separate Python executable or virtualenv inside Home Assistant.

### Install manually

Copy the `custom_components/tapo_trigger` directory into your Home Assistant config directory under `custom_components/tapo_trigger`, then restart Home Assistant.

### Configuration

The config flow asks for:

- camera host or IP
- either a cloud password or a username/password pair
- optional control port override
- update interval in seconds

After setup, the update interval can be changed from the integration options.

### Notes

- Credentials are stored by Home Assistant in the config entry, not in this repository.
- This integration is intentionally narrow: it only targets privacy mode, unlike broader Tapo integrations.
- If firmware or `pytapo` changes break privacy mode itself, that can still affect this integration.

## Root CLI script

### Local install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` is primarily for local development and script usage. It includes `pytapo`, `requests`, and a Home Assistant version constraint to keep local development aligned with the custom integration target.

### Usage

With third-party account credentials:

```bash
python privacy_mode.py 192.168.1.10 status --username USERNAME --password PASSWORD
python privacy_mode.py 192.168.1.10 test --username USERNAME --password PASSWORD
python privacy_mode.py 192.168.1.10 on --username USERNAME --password PASSWORD
python privacy_mode.py 192.168.1.10 off --username USERNAME --password PASSWORD
python privacy_mode.py 192.168.1.10 toggle --username USERNAME --password PASSWORD
```

With cloud-password auth:

```bash
python privacy_mode.py 192.168.1.10 status --cloud-password CLOUD_PASSWORD
python privacy_mode.py 192.168.1.10 toggle --cloud-password CLOUD_PASSWORD
```

If the camera needs KLAP on port 80:

```bash
python privacy_mode.py 192.168.1.10 toggle --cloud-password CLOUD_PASSWORD --port 80 --klap
```

Using environment variables:

```bash
export TAPO_USERNAME=USERNAME
export TAPO_PASSWORD=PASSWORD
python privacy_mode.py 192.168.1.10 status
```

The `test` action prints the raw `getPrivacyMode()` response without changing state.