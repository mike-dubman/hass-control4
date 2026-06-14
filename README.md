# hass-control4 (vendor fork)

Vendor fork of [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4), maintained for faster delivery of features not yet merged upstream.

**Versioning:** This fork uses **CalVer** (`YYYY.MM.DD.N`), not upstream semver. Example: `2026.06.13.1` = first build on 2026-06-13. See [Releases](https://github.com/mike-dubman/hass-control4/releases) for changelogs (including which upstream commit each build is based on).

This custom integration for Home Assistant allows control of Control4 lights, locks (only locks that are relay-based in Control4), alarm control panels, door/window/motion sensors (as binary sensors), thermostats, fans, relay devices (as switches), and blinds/shades (as covers, stateless open/close/stop).

## Installation

This repo is **not** in the default HACS store. Add it as a custom repository first:

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Repository: `https://github.com/mike-dubman/hass-control4`
3. Category: **Integration** → **Add**
4. **HACS** → **Integrations** → **Explore & Download Repositories** → find **Control4** → **Download**
5. **Restart Home Assistant**

Install the latest [release tag](https://github.com/mike-dubman/hass-control4/releases) (stable). Open pull requests against `release` publish a **pre-release debug drop** you can install from HACS with **Show beta versions** enabled.

Once installed, follow the same setup instructions as the default integration: https://www.home-assistant.io/integrations/control4

If the HACS readme looks stale after an update: **HACS** → **⋮** → **Clear cache**, restart HA, then **Redownload** the integration.

### Additional configuration required for alarm control panel

If you are using an alarm control panel, you must go to Home Assistant -> Configuration -> Devices and Services -> Integrations and click "Configure" on the Control4 entry.

In the dialog that appears, choose the Control4 alarm arming modes that you want to correspond to each Home Assistant arming mode. For example, a DSC alarm system uses "Stay" as the "Alarm arm home mode name", and "Away" as the "Alarm arm away mode name". If your alarm system does not use one of the mode names, select `(not set)`. Once you click submit on the dialog, Home Assistant will be able to arm your alarm control panel and detect its state.

## Releasing

Merging to `release` does **not** create a stable GitHub release automatically. Cut a release when you are ready to ship to HACS users.

### Before you release

1. Merge the PRs you want into `release`.
2. Set `custom_components/control4/manifest.json` `version` to a new CalVer value (`YYYY.MM.DD.N`).
3. Confirm CI is green on `release`.

The workflow reads that manifest version and creates tag **`v{version}`** (for example `v2026.06.14.0`). If the tag already exists, the run succeeds but skips creating a duplicate release.

### Option A: GitHub UI

1. Open [Actions → Release publish](https://github.com/mike-dubman/hass-control4/actions/workflows/release-publish.yml).
2. Click **Run workflow**.
3. **Branch:** `release` (runs the workflow definition from `release`).
4. **Ref to release:** `release` (default — `release` branch HEAD) or a commit SHA to pin the tag.
5. Click **Run workflow** and wait for the job to finish.
6. Verify the new tag under [Releases](https://github.com/mike-dubman/hass-control4/releases).

### Option B: CLI script

From a clone of this repo, with [GitHub CLI](https://cli.github.com/) authenticated (`gh auth login`):

```bash
chmod +x scripts/release-publish.sh   # once

# Release manifest version at release branch HEAD
./scripts/release-publish.sh

# Release manifest version at a specific commit on release
./scripts/release-publish.sh abc1234

# Trigger without waiting for the workflow to finish
RELEASE_WATCH=0 ./scripts/release-publish.sh
```

Optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_REPO` | `mike-dubman/hass-control4` | Fork to release |
| `RELEASE_WORKFLOW_BRANCH` | `release` | Branch that contains the workflow file |
| `RELEASE_WATCH` | `1` | Wait for workflow success (`0` to skip) |

## Upstream sync

| Branch | Purpose |
|--------|---------|
| `master` | Tracks [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4) `master` |
| `release` | Shipped vendor line (default branch; PRs target here; stable releases are cut manually) |

### Testing a pull request

Each PR to `release` triggers a pre-release tag (`v{version}-pr{number}.{sha}`). In HACS, enable **Show beta versions** for this repository, then install that tag from the Control4 update entity before merging.

For bugs in features that exist upstream, consider opening issues on [lawtancool/hass-control4](https://github.com/lawtancool/hass-control4/issues). For vendor-only features, use [this repo's issues](https://github.com/mike-dubman/hass-control4/issues).

## Disclaimer

This is **not** the official lawtancool integration or Home Assistant core integration. It is a community vendor fork under the Apache 2.0 license.

This integration is essentially a fuller version of the Control4 integration that is included in Home Assistant by default, and may receive updates faster than the default integration.

This means, however, that this custom integration may not be as stable as the default integration, as the code has not gone through Home Assistant's review process and contains newer features.

This integration is not affiliated with or endorsed by Control4.
