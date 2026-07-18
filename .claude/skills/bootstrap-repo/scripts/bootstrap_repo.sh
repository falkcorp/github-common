#!/usr/bin/env bash
# Bootstrap a GitHub repository to ghcommon standards.
#
# Modes:
#   create — gh repo create + apply standards from empty
#   adopt  — apply standards to an existing repo
#
# Flavors: action | library | service | cli
#
# Usage:
#   bootstrap_repo.sh --flavor {action|library|service|cli} \
#                     --mode {create|adopt} \
#                     --name REPO \
#                     [--owner jdfalk] [--private|--public] \
#                     [--ghcommon PATH] [--repo-path PATH] \
#                     [--skip-protection] [--skip-labels]
#
# See references/repo-settings.md and references/branch-protection.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------- argument parsing ----------

FLAVOR=""
MODE=""
OWNER="jdfalk"
NAME=""
VISIBILITY="--private"
GHCOMMON=""
REPO_PATH=""
SKIP_PROTECTION=0
SKIP_LABELS=0

usage() {
  sed -n '2,18p' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
  --flavor)
    FLAVOR="$2"
    shift 2
    ;;
  --mode)
    MODE="$2"
    shift 2
    ;;
  --owner)
    OWNER="$2"
    shift 2
    ;;
  --name)
    NAME="$2"
    shift 2
    ;;
  --private)
    VISIBILITY="--private"
    shift
    ;;
  --public)
    VISIBILITY="--public"
    shift
    ;;
  --ghcommon)
    GHCOMMON="$2"
    shift 2
    ;;
  --repo-path)
    REPO_PATH="$2"
    shift 2
    ;;
  --skip-protection)
    SKIP_PROTECTION=1
    shift
    ;;
  --skip-labels)
    SKIP_LABELS=1
    shift
    ;;
  -h | --help) usage ;;
  *)
    echo "unknown arg: $1" >&2
    usage
    ;;
  esac
done

[[ -z ${FLAVOR} ]] && {
  echo "error: --flavor required" >&2
  exit 2
}
[[ -z ${MODE} ]] && {
  echo "error: --mode required" >&2
  exit 2
}
[[ -z ${NAME} ]] && {
  echo "error: --name required" >&2
  exit 2
}

case "${FLAVOR}" in action | library | service | cli) ;; *)
  echo "error: --flavor must be action, library, service, or cli" >&2
  exit 2
  ;;
esac
case "${MODE}" in create | adopt) ;; *)
  echo "error: --mode must be create or adopt" >&2
  exit 2
  ;;
esac

# ---------- resolve ghcommon path ----------

if [[ -z ${GHCOMMON} ]]; then
  GHCOMMON="${GHCOMMON_PATH:-$HOME/repos/github.com/jdfalk/ghcommon}"
fi
if [[ ! -d "${GHCOMMON}/.github/instructions" ]]; then
  echo "error: ghcommon not found at ${GHCOMMON}" >&2
  echo "       set --ghcommon PATH or GHCOMMON_PATH env var" >&2
  exit 1
fi
echo "→ Using ghcommon at: ${GHCOMMON}"

# ---------- create or verify repo ----------

if [[ ${MODE} == "create" ]]; then
  echo "→ Creating ${OWNER}/${NAME} (${VISIBILITY#--})"
  if gh repo view "${OWNER}/${NAME}" >/dev/null 2>&1; then
    echo "error: repo already exists; use --mode adopt" >&2
    exit 1
  fi
  # Try template if it exists for this flavor; fall back to empty.
  TEMPLATE="${OWNER}/jft-${FLAVOR}-template"
  if gh repo view "${TEMPLATE}" >/dev/null 2>&1; then
    echo "→ Creating from template ${TEMPLATE}"
    gh repo create "${OWNER}/${NAME}" "${VISIBILITY}" --template "${TEMPLATE}"
  else
    echo "→ Template ${TEMPLATE} not found; creating empty"
    gh repo create "${OWNER}/${NAME}" "${VISIBILITY}" --add-readme
  fi
else
  if ! gh repo view "${OWNER}/${NAME}" >/dev/null 2>&1; then
    echo "error: ${OWNER}/${NAME} not found; use --mode create" >&2
    exit 1
  fi
  echo "→ Adopting existing ${OWNER}/${NAME}"
fi

# ---------- ensure local checkout ----------

if [[ -z ${REPO_PATH} ]]; then
  REPO_PATH="$(mktemp -d "/tmp/bootstrap-${NAME}.XXXXXX")"
  echo "→ Cloning into ${REPO_PATH}"
  gh repo clone "${OWNER}/${NAME}" "${REPO_PATH}" -- --quiet
  CLEANUP_REPO_PATH=1
else
  echo "→ Using local checkout at ${REPO_PATH}"
  CLEANUP_REPO_PATH=0
fi

# ---------- apply repo settings ----------

"${SCRIPT_DIR}/apply_repo_settings.sh" "${OWNER}" "${NAME}"

# ---------- sync standard files from ghcommon ----------

echo "→ Syncing instruction/dependabot/AGENTS files from ghcommon"
SYNC_SCRIPT="${GHCOMMON}/scripts/sync-repo-setup.py"
if [[ -f ${SYNC_SCRIPT} ]]; then
  python3 "${SCRIPT_DIR}/_sync_one_repo.py" "${GHCOMMON}" "${REPO_PATH}" ||
    echo "  (sync shim failed; continuing)"
else
  echo "  (sync-repo-setup.py not found at ${SYNC_SCRIPT}; skipping)"
fi

# ---------- sync labels ----------

if [[ ${SKIP_LABELS} -eq 0 ]]; then
  echo "→ Syncing labels from ghcommon/labels.json"
  LABEL_SCRIPT="${GHCOMMON}/scripts/sync-github-labels.py"
  if [[ -f ${LABEL_SCRIPT} ]]; then
    # ghcommon's sync-github-labels.py reads PAT_TOKEN or GITHUB_TOKEN, not GH_TOKEN
    GITHUB_TOKEN="${PAT_TOKEN:-${GITHUB_TOKEN:-$(gh auth token)}}" \
      python3 "${LABEL_SCRIPT}" "${OWNER}" "${NAME}" \
      --labels-file "${GHCOMMON}/labels.json" ||
      echo "  (sync-github-labels.py failed; continuing)"
  fi
fi

# ---------- flavor overlay ----------

echo "→ Applying flavor overlay: ${FLAVOR}"
case "${FLAVOR}" in
action)
  # action.yml stub if missing
  if [[ ! -f "${REPO_PATH}/action.yml" ]]; then
    cat >"${REPO_PATH}/action.yml" <<EOF
name: '${NAME}'
description: 'TODO: describe this action'
runs:
  using: 'composite'
  steps:
    - run: echo "TODO: implement ${NAME}"
      shell: bash
EOF
  fi
  [[ -f "${REPO_PATH}/TODO.md" ]] || echo "# TODO" >"${REPO_PATH}/TODO.md"
  ;;
library)
  if [[ ! -f "${REPO_PATH}/CHANGELOG.md" ]]; then
    cat >"${REPO_PATH}/CHANGELOG.md" <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- scriv-insert-here -->
EOF
  fi
  ;;
service)
  if [[ ! -f "${REPO_PATH}/Dockerfile" ]]; then
    cat >"${REPO_PATH}/Dockerfile" <<'EOF'
# TODO: choose a base image
FROM scratch
# TODO: COPY artifacts and set ENTRYPOINT
EOF
  fi
  ;;
cli)
  # CLI / distributable binary. No Dockerfile (binary is shipped via goreleaser
  # / brew / winget, not containers). Same CHANGELOG seed as library.
  if [[ ! -f "${REPO_PATH}/CHANGELOG.md" ]]; then
    cat >"${REPO_PATH}/CHANGELOG.md" <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- scriv-insert-here -->
EOF
  fi
  ;;
esac

# ---------- seed repository-config.yml ----------

CONFIG_FILE="${REPO_PATH}/.github/repository-config.yml"
if [[ ! -f ${CONFIG_FILE} ]]; then
  mkdir -p "$(dirname "${CONFIG_FILE}")"
  cat >"${CONFIG_FILE}" <<EOF
# file: .github/repository-config.yml
# Seeded by bootstrap-repo skill on $(date -u +%Y-%m-%d)

repository:
  name: ${NAME}
  type: ${FLAVOR}
  primary_language: auto
  description: ''
EOF
fi

# ---------- commit & push ----------

cd "${REPO_PATH}"
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git -c user.name="ghcommon-bootstrap" -c user.email="bootstrap@ghcommon.local" \
    commit -m "chore: bootstrap repo to ghcommon standards (${FLAVOR})"
  git push origin HEAD:main || git push -u origin HEAD
  echo "✓ Pushed bootstrap commit"
else
  echo "→ No file changes to commit"
fi

# ---------- apply branch protection (after commit so main exists) ----------

if [[ ${SKIP_PROTECTION} -eq 0 ]]; then
  "${SCRIPT_DIR}/apply_branch_protection.sh" "${OWNER}" "${NAME}" "${REPO_PATH}"
else
  echo "→ Skipping branch protection (--skip-protection)"
fi

# ---------- verify ----------

"${SCRIPT_DIR}/verify_bootstrap.sh" --owner "${OWNER}" --repo "${NAME}" \
  --repo-path "${REPO_PATH}" --flavor "${FLAVOR}"

# ---------- update registry ----------

REGISTRY="${GHCOMMON}/.github/bootstrapped-repos.json"
python3 "${SCRIPT_DIR}/_update_registry.py" \
  --registry "${REGISTRY}" \
  --owner "${OWNER}" --name "${NAME}" \
  --flavor "${FLAVOR}" --mode "${MODE}"
echo "→ Registry updated: ${REGISTRY}"
echo "  (commit ghcommon/.github/bootstrapped-repos.json to record this bootstrap)"

# ---------- next steps ----------

cat <<EOF

✅ Bootstrap complete: ${OWNER}/${NAME}

Next steps (manual):
  1. Run setup-ci-app.sh in the repo to create/link the GitHub App for releases.
     (Tracked: future automation in ghcommon issue #264)
  2. Verify secrets exist: gh secret list -R ${OWNER}/${NAME}
     Expected (if release workflows used): CI_APP_ID, CI_APP_PRIVATE_KEY
  3. Review the bootstrap commit and adjust flavor-overlay stubs as needed.

Local checkout: ${REPO_PATH}
EOF

if [[ ${CLEANUP_REPO_PATH} -eq 1 ]]; then
  echo "  (Temp checkout will remain at ${REPO_PATH} for review.)"
fi
