#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${BRUH_PYTHON_BIN:-$repo_root/.venv/bin/python}"
output_dir="$repo_root/build/macos-backend"
codesign_identity=""

usage() {
    cat <<'EOF'
Usage: scripts/build_macos_backend.sh [options]

Builds a self-contained `bruh` command-line backend for the macOS app.

Options:
  --output DIRECTORY       Bundle output directory (default: build/macos-backend)
  --codesign-identity ID   Sign bundled Python binaries with this identity
  -h, --help               Show this help

Set BRUH_PYTHON_BIN to use a Python interpreter other than .venv/bin/python.
Install the release build tools first:
  .venv/bin/python -m pip install -e '.[release]'
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            output_dir="$2"
            shift 2
            ;;
        --codesign-identity)
            codesign_identity="$2"
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

if [[ ! -x "$python_bin" ]]; then
    echo "Python interpreter not found: $python_bin" >&2
    echo "Create .venv and install the release tools first." >&2
    exit 1
fi

if ! "$python_bin" -m PyInstaller --version >/dev/null 2>&1; then
    echo "PyInstaller is not installed for $python_bin." >&2
    echo "Run: $python_bin -m pip install -e '.[release]'" >&2
    exit 1
fi

if [[ "$output_dir" == "/" || "$output_dir" == "$repo_root" ]]; then
    echo "Refusing to overwrite unsafe output directory: $output_dir" >&2
    exit 1
fi

build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

pyinstaller_args=(
    --noconfirm
    --clean
    --onedir
    --name bruh
    --distpath "$build_dir/dist"
    --workpath "$build_dir/work"
    --specpath "$build_dir/spec"
    --paths "$repo_root/src"
    --hidden-import bruhagent.llm.gemini_provider
    --hidden-import bruhagent.llm.ollama_provider
    --collect-all google.genai
    --collect-all ollama
    --copy-metadata google-genai
    --copy-metadata ollama
    --copy-metadata pydantic
)

if [[ -n "$codesign_identity" ]]; then
    pyinstaller_args+=(--codesign-identity "$codesign_identity")
fi

"$python_bin" -m PyInstaller "${pyinstaller_args[@]}" "$repo_root/src/bruhagent/cli.py"

rm -rf "$output_dir"
mkdir -p "$(dirname "$output_dir")"
ditto "$build_dir/dist/bruh" "$output_dir"

echo "Built bundled backend: $output_dir"
