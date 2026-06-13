# hass-control4 (vendor fork)

Vendor fork of [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4), maintained for faster delivery of features not yet merged upstream. Install from the **`release`** branch (default) or the latest [release tag](https://github.com/mike-dubman/hass-control4/releases).

This custom integration for Home Assistant allows control of Control4 lights, locks (only locks that are relay-based in Control4), alarm control panels, door/window/motion sensors (as binary sensors), thermostats, fans, relay devices (as switches), and blinds/shades (as covers, stateless open/close/stop).

## Installation

First, add this repository as a [custom repository](https://www.hacs.xyz/docs/faq/custom_repositories/) in HACS:

- URL: `https://github.com/mike-dubman/hass-control4`
- Category: **Integration**

Then install through HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mike-dubman&repository=hass-control4)

Once installed, follow the same setup instructions as the default integration: https://www.home-assistant.io/integrations/control4

### Additional configuration required for alarm control panel

If you are using an alarm control panel, you must go to Home Assistant -> Configuration -> Devices and Services -> Integrations and click "Configure" on the Control4 entry.

In the dialog that appears, choose the Control4 alarm arming modes that you want to correspond to each Home Assistant arming mode. For example, a DSC alarm system uses "Stay" as the "Alarm arm home mode name", and "Away" as the "Alarm arm away mode name". If your alarm system does not use one of the mode names, select `(not set)`. Once you click submit on the dialog, Home Assistant will be able to arm your alarm control panel and detect its state.

## Upstream sync

| Branch | Purpose |
|--------|---------|
| `master` | Tracks [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4) `master` |
| `release` | Shipped vendor line (default branch, HACS installs, version tags) |

For bugs in features that exist upstream, consider opening issues on [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4/issues). For vendor-only features, use [this repo's issues](https://github.com/mike-dubman/hass-control4/issues).

## Disclaimer

This is **not** the official lawtancool integration or Home Assistant core integration. It is a community vendor fork under the Apache 2.0 license.

This integration is essentially a fuller version of the Control4 integration that is included in Home Assistant by default, and may receive updates faster than the default integration.

This means, however, that this custom integration may not be as stable as the default integration, as the code has not gone through Home Assistant's review process and contains newer features.

This integration is not affiliated with or endorsed by Control4.
