# Bruh Agent for macOS

## Development

1. Install Xcode.
2. From the repository root, create the Python environment and install Bruh:

   ```zsh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -e .
   ```

3. Open `BruhAgent.xcodeproj` in Xcode.
4. Configure stable Debug signing before granting Full Disk Access:

   - Select the **BruhAgent** target and open **Signing & Capabilities**.
   - Choose your Apple Developer or Personal Team.
   - In **Build Settings**, set **Code Signing Identity** for **Debug** to
     `Apple Development`, not `Sign to Run Locally`.

   Ad-hoc local signing changes the app identity on every build, which makes
   macOS forget its Full Disk Access permission.

5. In **Product > Scheme > Edit Scheme > Run > Arguments**, add this enabled
   environment variable:

   ```text
   BRUH_EXECUTABLE=/absolute/path/to/bruh-agent/.venv/bin/bruh
   ```

   Replace `/absolute/path/to/bruh-agent` with the folder where you cloned the
   repository.

6. Build and run the app with `Command-R`.
7. To let the app read Messages, add the debug `BruhAgent.app` build to
   **System Settings > Privacy & Security > Full Disk Access**. In Xcode, use
   **Product > Show Build Folder in Finder** to locate it.
8. Rebuild the app.

## Release builds

Bruh Agent is distributed directly, not through the Mac App Store. It requires
Full Disk Access to read the Messages database and therefore does not use App
Sandbox.

The repository stores only source code. The Python backend, `.app` archive, and
release DMG are generated locally and ignored by Git.

1. Install release build tools:

   ```zsh
   .venv/bin/python -m pip install -e '.[release]'
   ```

2. Install a **Developer ID Application** certificate in Keychain. In Xcode,
   select that identity for the Release configuration.

3. Build, sign, and archive the app. Replace the certificate name with the one
   shown by `security find-identity -v -p codesigning`:

   ```zsh
   scripts/archive_macos_app.sh \
     --signing-identity "Developer ID Application: Your Name (TEAMID)"
   ```

   The script packages Python and its dependencies with PyInstaller, embeds the
   result at `BruhAgent.app/Contents/Resources/backend`, archives the app, and
   creates a DMG under `build/release/`.

4. For a public release, notarize and staple it by adding a `notarytool`
   Keychain profile. Create it once with an Apple ID app-specific password:

   ```zsh
   xcrun notarytool store-credentials "bruh-agent-notary" \
     --apple-id "you@example.com" \
     --team-id "YOUR_TEAM_ID"
   ```

   The command securely prompts for the app-specific password and saves the
   resulting profile in Keychain.

   Then build and notarize:

   ```zsh
   scripts/archive_macos_app.sh \
     --signing-identity "Developer ID Application: Your Name (TEAMID)" \
     --notary-profile "bruh-agent-notary"
   ```

   Upload the resulting DMG to the matching GitHub Release. Build from the Git
   tag you intend to release, not from an uncommitted working tree.

The first release targets the architecture of the Mac that builds it. Build on
Apple Silicon for an arm64 release; Intel support requires a separate build.
