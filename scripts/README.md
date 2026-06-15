# Releasing

Stable GitHub releases for this fork are **manual**. Merging PRs to `release` does not create a release tag by itself.

PRs to `release` still get automatic **pre-release debug drops** (`v{version}-pr{number}.{sha}`) for HACS beta testing.

**Manifest during a PR:** bump `version` **once** when the PR is ready to merge (or at open if you need a distinct debug-drop CalVer). Do not increment the patch on every fix commit in the same PR.

## Before you release

1. Merge the PRs you want into `release`.
2. Set `custom_components/control4/manifest.json` `version` to a new CalVer value (`YYYY.MM.DD.N`).
3. Confirm CI is green on `release`.

The **Release publish** workflow reads that manifest version and creates tag **`v{version}`** (for example `v2026.06.14.0`). If the tag already exists, the run succeeds but skips creating a duplicate release.

## Option A: GitHub UI

1. Open [Actions → Release publish](https://github.com/mike-dubman/hass-control4/actions/workflows/release-publish.yml).
2. Click **Run workflow**.
3. **Branch:** `release` (runs the workflow definition from `release`).
4. **Ref to release:** `release` (default — `release` branch HEAD) or a commit SHA to pin the tag.
5. Click **Run workflow** and wait for the job to finish.
6. Verify the new tag under [Releases](https://github.com/mike-dubman/hass-control4/releases).

## Option B: CLI script

From the repo root, with [GitHub CLI](https://cli.github.com/) authenticated (`gh auth login`):

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

## Example: batch several PRs into one release

1. Merge PR #3 and PR #4 to `release`.
2. Bump manifest once on `release` (e.g. `2026.06.14.0`).
3. Run `./scripts/release-publish.sh` once → single tag `v2026.06.14.0`.
