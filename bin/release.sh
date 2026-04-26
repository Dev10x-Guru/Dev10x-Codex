#!/usr/bin/env bash
# Release workflow for Dev10x.
#
# Develop uses .dev0 suffixes between releases (e.g. 0.7.0.dev0).
# The release script strips .dev0 to produce the release version,
# tags it, resets main, and bumps develop to the next dev version.
#
# Usage: ./bin/release.sh {features|fixes|major}
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RESET='\033[0m'

VERSION_FILES=".bumpversion.toml .claude-plugin/plugin.json pyproject.toml uv.lock"

command -v bump-my-version >/dev/null || {
    echo "bump-my-version not found. Install: pip install bump-my-version" >&2
    exit 1
}
command -v gh >/dev/null || {
    echo "gh not found. Install: https://cli.github.com" >&2
    exit 1
}

function current_version {
    bump-my-version show current_version
}

function header {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${CYAN}  $1${RESET}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

function step {
    echo -e "  ${GREEN}▸${RESET} $1"
}

function sync_branches {
    header "Phase 1 · Synchronize branches"
    step "Checking out develop..."
    git checkout develop
    git pull origin develop
    step "Checking out main..."
    git checkout main
    git pull origin main
    step "Rebasing develop on main..."
    git checkout develop
    git rebase main
}

function finalize_version {
    local current
    current=$(current_version)
    local release="${current%.dev*}"
    if [[ "$current" == "$release" ]]; then
        echo "⚠️  Version $current has no dev suffix — nothing to finalize" >&2
        exit 1
    fi
    step "Finalizing: ${current} → ${release}"
    bump-my-version bump --new-version "$release" --no-tag --no-commit
    git add $VERSION_FILES
    git commit -m "🔖 Bump version: ${current} → ${release}"
}

function bump_version {
    local version_type=$1
    local before
    before=$(current_version)
    bump-my-version bump "$version_type" --no-tag --no-commit
    local after
    after=$(current_version)
    step "Bumping: ${before} → ${after}"
    git add $VERSION_FILES
    git commit -m "🔖 Bump version: ${before} → ${after}"
}

function release {
    local pre_bump="${1:-}"

    header "Phase 2 · Prepare release version"
    if [[ -n "$pre_bump" ]]; then
        bump_version "$pre_bump"
    fi
    finalize_version

    local tag="v$(current_version)"

    header "Phase 3 · Tag and push"
    step "Creating tag: $tag"
    git tag -f "$tag" -m "Release $tag"
    git push origin "$tag"

    step "Resetting main to develop HEAD..."
    git checkout main
    git reset --hard develop
    git checkout develop

    header "Phase 4 · Advance develop to next dev version"
    bump_version "minor"
    step "Pushing develop and main..."
    git push origin develop
    git push origin main

    header "Phase 5 · Create GitHub release"
    git checkout main
    step "Creating release for $tag..."
    gh release create "$tag" --generate-notes
    git checkout develop

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${GREEN}  ✅ Released $tag${RESET}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

case "${1:-}" in
    major)
        echo -e "${YELLOW}🎉 Releasing new major version...${RESET}"
        sync_branches
        release "major"
        ;;
    features)
        echo -e "${YELLOW}🎉 Releasing new minor version (features)...${RESET}"
        sync_branches
        release
        ;;
    fixes)
        echo -e "${YELLOW}🎉 Releasing new patch version (fixes)...${RESET}"
        sync_branches
        release "patch"
        ;;
    *)
        echo "Usage: $0 {major|features|fixes}"
        echo ""
        echo "  features  Strip .dev0, tag, release, bump to next minor .dev0"
        echo "  fixes     Bump patch, strip .dev0, tag, release, bump to next minor .dev0"
        echo "  major     Bump major, strip .dev0, tag, release, bump to next minor .dev0"
        exit 1
        ;;
esac
