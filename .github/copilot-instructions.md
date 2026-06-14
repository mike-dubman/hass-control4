# Copilot code review instructions

This repository is a Home Assistant custom integration that overrides the core `control4` domain.

When reviewing pull requests:

- Prefer minimal, focused diffs; flag unrelated changes.
- Config flow uses a temporary workaround for frontend translation collisions; see `config_flow.py` and https://github.com/home-assistant/frontend/issues/52600.
- Custom integrations must keep `manifest.json` keys sorted (domain, name, then alphabetical) for hassfest.
- Do not suggest renaming the integration domain unless a migration plan is included.
