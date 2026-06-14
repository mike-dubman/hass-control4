#!/usr/bin/env bash
# Trigger the Release publish GitHub Actions workflow (manual stable release).
#
# Usage:
#   ./scripts/release-publish.sh              # tag manifest version at release branch HEAD
#   ./scripts/release-publish.sh abc1234      # tag manifest version at a specific commit
#   RELEASE_WATCH=0 ./scripts/release-publish.sh
#
# Requires: gh auth login (repo + workflow scopes)
set -euo pipefail

REPO="${GITHUB_REPO:-mike-dubman/hass-control4}"
WORKFLOW="${RELEASE_WORKFLOW:-release-publish.yml}"
WORKFLOW_BRANCH="${RELEASE_WORKFLOW_BRANCH:-release}"
REF="${1:-release}"
WATCH="${RELEASE_WATCH:-1}"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI is required (https://cli.github.com/)" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: run 'gh auth login' first" >&2
  exit 1
fi

echo "Repository:  ${REPO}"
echo "Workflow:    ${WORKFLOW} (from branch ${WORKFLOW_BRANCH})"
echo "Release ref: ${REF}"
echo

VERSION=$(gh api "repos/${REPO}/contents/custom_components/control4/manifest.json?ref=${REF}" --jq .content 2>/dev/null | base64 -d | jq -r .version 2>/dev/null || true)
if [[ -n "${VERSION}" ]]; then
  echo "Manifest version at ${REF}: ${VERSION} → tag v${VERSION}"
  echo
fi

gh workflow run "${WORKFLOW}" \
  --repo "${REPO}" \
  --ref "${WORKFLOW_BRANCH}" \
  -f "ref=${REF}"

echo "Release publish workflow triggered."
echo "Actions: https://github.com/${REPO}/actions/workflows/${WORKFLOW}"

if [[ "${WATCH}" == "1" ]]; then
  sleep 3
  RUN_ID=$(gh run list --repo "${REPO}" --workflow "${WORKFLOW}" --limit 1 --json databaseId --jq '.[0].databaseId')
  if [[ -n "${RUN_ID}" && "${RUN_ID}" != "null" ]]; then
    echo "Watching run ${RUN_ID}..."
    gh run watch "${RUN_ID}" --repo "${REPO}" --exit-status
  fi
fi
