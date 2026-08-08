#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_path="$repo_root/macos/BruhAgent/BruhAgent.xcodeproj"
scheme="BruhAgent"
archive_path="$repo_root/build/BruhAgent.xcarchive"
release_dir="$repo_root/build/release"
signing_identity=""
notary_profile=""

usage() {
    cat <<'EOF'
Usage: scripts/archive_macos_app.sh --signing-identity ID [options]

Builds the bundled Python backend, archives the macOS app, signs it with a
Developer ID identity, and creates a distributable DMG.

Options:
  --signing-identity ID  Developer ID Application certificate name (required)
  --notary-profile NAME  Optional `notarytool` Keychain profile. When supplied,
                         the script notarizes and staples the DMG.
  -h, --help             Show this help

Before running:
  1. Install release tools: .venv/bin/python -m pip install -e '.[release]'
  2. Install a Developer ID Application certificate in Keychain.
  3. If notarizing, create a notarytool Keychain profile.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --signing-identity)
            signing_identity="$2"
            shift 2
            ;;
        --notary-profile)
            notary_profile="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ -z "$signing_identity" ]]; then
    echo "--signing-identity is required." >&2
    usage >&2
    exit 2
fi

if ! security find-identity -v -p codesigning | grep -Fq "$signing_identity"; then
    echo "Code-signing identity not found: $signing_identity" >&2
    exit 1
fi

"$repo_root/scripts/build_macos_backend.sh" \
    --codesign-identity "$signing_identity"

rm -rf "$archive_path" "$release_dir"
mkdir -p "$release_dir"

xcodebuild archive \
    -project "$project_path" \
    -scheme "$scheme" \
    -configuration Release \
    -destination 'generic/platform=macOS' \
    -archivePath "$archive_path" \
    CODE_SIGN_STYLE=Manual \
    CODE_SIGN_IDENTITY="$signing_identity"

app_path="$archive_path/Products/Applications/BruhAgent.app"
backend_path="$app_path/Contents/Resources/backend"
if [[ ! -d "$app_path" ]]; then
    echo "Archived app not found: $app_path" >&2
    exit 1
fi

mkdir -p "$(dirname "$backend_path")"
ditto "$repo_root/build/macos-backend" "$backend_path"

# PyInstaller signs all collected binaries first. Re-signing the parent app now
# seals the copied backend into the final Developer ID signature.
codesign --force --options runtime --timestamp \
    --sign "$signing_identity" "$app_path"
codesign --verify --deep --strict --verbose=2 "$app_path"

marketing_version="$(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleShortVersionString' "$archive_path/Info.plist")"
dmg_staging_dir="$(mktemp -d)"
trap 'rm -rf "$dmg_staging_dir"' EXIT
dmg_path="$release_dir/BruhAgent-$marketing_version-macos.dmg"

ditto "$app_path" "$dmg_staging_dir/BruhAgent.app"
ln -s /Applications "$dmg_staging_dir/Applications"
hdiutil create \
    -volname "Bruh Agent" \
    -srcfolder "$dmg_staging_dir" \
    -ov \
    -format UDZO \
    "$dmg_path"

if [[ -n "$notary_profile" ]]; then
    xcrun notarytool submit "$dmg_path" --keychain-profile "$notary_profile" --wait
    xcrun stapler staple "$dmg_path"
    xcrun stapler validate "$dmg_path"
fi

echo "Release DMG: $dmg_path"
