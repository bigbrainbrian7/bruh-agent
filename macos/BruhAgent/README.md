# Developing the macOS app

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
8. Rebuild the app
