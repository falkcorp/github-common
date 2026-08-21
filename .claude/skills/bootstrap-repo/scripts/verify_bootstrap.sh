#!/usr/bin/env bash
# Verify a repository matches ghcommon bootstrap expectations.
# Reads back repo settings + branch protection via gh api and diffs against
# the canonical payload from references/repo-settings.md and branch-protection.md.
#
# Exits 0 on full match, 1 on any drift, 2 on usage error.
#
# Usage:
#   verify_bootstrap.sh --owner OWNER --repo REPO \
#                       [--flavor FLAVOR]

set -euo pipefail

OWNER=""
REPO=""
FLAVOR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  --owner)
    OWNER="$2"
    shift 2
    ;;
  --repo)
    REPO="$2"
    shift 2
    ;;
  --flavor)
    FLAVOR="$2"
    shift 2
    ;;
  *)
    echo "unknown arg: $1" >&2
    exit 2
    ;;
  esac
done

[[ -z ${OWNER} || -z ${REPO} ]] && {
  echo "usage: $0 --owner OWNER --repo REPO [--flavor FLAVOR]" >&2
  exit 2
}

DRIFT=0

# ---------- repo settings ----------

EXPECTED_SETTINGS=$(
  cat <<'JSON'
{
  "allow_merge_commit": false,
  "allow_squash_merge": false,
  "allow_rebase_merge": true,
  "allow_auto_merge": true,
  "delete_branch_on_merge": false,
  "allow_update_branch": true,
  "has_issues": true,
  "has_projects": false,
  "has_wiki": false,
  "web_commit_signoff_required": false
}
JSON
)

echo "→ Checking repo settings on ${OWNER}/${REPO}"
ACTUAL=$(gh api "repos/${OWNER}/${REPO}")
while IFS= read -r key; do
  expected=$(echo "${EXPECTED_SETTINGS}" | jq -r ".${key}")
  actual=$(echo "${ACTUAL}" | jq -r ".${key}")
  if [[ ${expected} != "${actual}" ]]; then
    echo "  ✗ ${key}: expected=${expected} actual=${actual}"
    DRIFT=1
  fi
done < <(echo "${EXPECTED_SETTINGS}" | jq -r 'keys[]')

if [[ ${DRIFT} -eq 0 ]]; then
  echo "  ✓ Repo settings match"
fi

# ---------- branch protection (must be ABSENT) ----------
#
# falkcorp manages branch rules with ORG-WIDE RULESETS. Classic per-repo
# protection is not just redundant here, it is harmful: it has no bypass_actors
# list at all, so org automation cannot be exempted from it. Measured 2026-08-21
# — classic protection on 15 repos blocked the template-sync bot's push to main
# for ~4 months (GH006 "Changes must be made through a pull request"), and the
# contexts this skill used to install were job IDs, which GitHub never reports
# (it reports display names), so every required check sat "Expected" forever and
# 34 Dependabot PRs were unmergeable. Deleting classic protection fixed both.
#
# So this is now a NEGATIVE check: its presence is drift.

echo "→ Checking that classic branch protection is ABSENT on ${OWNER}/${REPO}:main"
# NB: test the EXIT STATUS, not the output. `gh api` prints HTTP error bodies to
# STDOUT, so a 404 still yields a non-empty string:
#   {"message":"Branch not protected","status":"404"}
# Capturing stdout and testing -n/-z therefore reports "protected" for every
# repo, protected or not. The pre-2026-08-21 version of this check had the same
# bug inverted and could never detect missing protection.
if gh api "repos/${OWNER}/${REPO}/branches/main/protection" >/dev/null 2>&1; then
  echo "  ✗ classic branch protection is present — it should be removed."
  echo "    Branch rules belong in the org-wide ruleset, not per-repo protection."
  echo "    Remove with:"
  echo "      gh api -X DELETE repos/${OWNER}/${REPO}/branches/main/protection"
  DRIFT=1
else
  echo "  ✓ No classic branch protection (org rulesets govern main)"
fi

# ---------- summary ----------

if [[ ${DRIFT} -eq 0 ]]; then
  echo ""
  echo "✅ ${OWNER}/${REPO} is bootstrap-compliant${FLAVOR:+ (${FLAVOR})}"
  exit 0
else
  echo ""
  echo "❌ ${OWNER}/${REPO} has drift; re-run bootstrap_repo.sh to fix"
  exit 1
fi
