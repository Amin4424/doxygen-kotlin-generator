# Kotlin Doxygen Filter

A clean, production-ready, standalone command-line tool that acts as an **input filter for Doxygen**, allowing you to generate API documentation for Kotlin projects as easily as possible.

---

## Why this exists

Doxygen does not natively support Kotlin. However, Kotlin is structurally very similar to Java. This tool processes Kotlin source files (`.kt`) on-the-fly and generates equivalent Java-like stub declarations to stdout. 

By combining this filter with Doxygen's `EXTENSION_MAPPING = kt=Java` configuration, Doxygen parses the filtered output as if it were Java, producing high-quality documentation that preserves:
- Classes, interfaces, enums, objects, and companion objects.
- Primary and secondary constructors.
- Properties (`val`, `var`) with type inference.
- Standard, suspend, and extension functions.
- Visibility modifiers (`public`, `protected`, `private`).
- Nullable types and generic declarations.
- KDoc comments (`/** ... */`) and Unicode descriptions.

---

## Installation

### Download Portable Binaries
Download the precompiled, standalone binary for your platform from [GitHub Releases](https://github.com/Amin4424/doxygen-kotlin-generator/releases):
- **Windows**: `kotlin-doxygen-windows-x64.exe`
- **Linux**: `kotlin-doxygen-linux-x64`
- **macOS**:
  - `kotlin-doxygen-macos-x64` (Intel)
  - `kotlin-doxygen-macos-arm64` (Apple Silicon)

Put the binary somewhere in your system path, or reference its absolute path directly in your `Doxyfile`.

---

## Integration with Doxyfile

To document Kotlin files in your project, add or update the following settings in your `Doxyfile`:

```ini
# Add .kt files to the inputs
FILE_PATTERNS          = *.kt *.java *.md

# Map Kotlin files to Java parser
EXTENSION_MAPPING      = kt=Java

# Run the filter for all Kotlin files (Windows)
FILTER_PATTERNS        = *.kt="C:/path/to/kotlin-doxygen-windows-x64.exe"

# Run the filter for all Kotlin files (Linux/macOS)
# FILTER_PATTERNS        = *.kt="/usr/local/bin/kotlin-doxygen-linux-x64"

# Ensure Doxygen processes the filtered source code
FILTER_SOURCE_FILES    = YES
```

### Why `FILTER_PATTERNS` is preferred over `INPUT_FILTER`
- `FILTER_PATTERNS = *.kt="..."` runs the filter **only** for `.kt` files.
- `INPUT_FILTER = "..."` executes the filter script on **all** files (including `.java`, `.md`, `.cpp`), which is slower and can corrupt the documentation parsing of already-supported languages.

---

## CLI Usage

The executable works as a standard CLI:

```bash
# Print help usage
kotlin-doxygen --help

# Print version
kotlin-doxygen --version

# Process a Kotlin file and print Java-like stub output to stdout
kotlin-doxygen path/to/File.kt
```

### Exit Codes:
- `0` on successful parsing.
- Non-zero on errors (e.g., file not found). Errors are written to `stderr`.

---

## Local Development & Build

This project requires **Python 3.10+** for local development.

### Setup and Testing
1. Clone the repository and navigate to its directory.
2. Build local standalone executables:
   - **Windows**:
     ```powershell
     .\scripts\build-windows.ps1
     ```
     This script creates a virtual environment, installs dependencies, runs tests, compiles the standalone binary using PyInstaller, and saves it to `dist/kotlin-doxygen.exe`.
   - **Linux/macOS**:
     ```bash
     ./scripts/build.sh
     ```
     This compiles the standalone binary to `dist/kotlin-doxygen`.

3. Run python unit tests manually:
   ```bash
   python -m unittest discover -s tests
   ```

---

## How it works (Example)

Given the following Kotlin file:
```kotlin
package com.example

/**
 * A sample Kotlin class.
 */
class Greeter(val greeting: String) {
    /**
     * Greet someone.
     */
    fun greet(name: String? = null): String {
        return "$greeting, ${name ?: "World"}"
    }

    /**
     * Extension function.
     */
    fun String.shout(): String = this.uppercase()
}
```

The filter outputs the following Java stub to `stdout`:
```java
package com.example;

/**
 * A sample Kotlin class.
 */
public class Greeter {
    public final String greeting;
    public Greeter(String greeting) {}

    /**
     * Greet someone.
     */
    public String greet(String name) {}

    /**
     * Extension function.
     */
    public static String shout(String receiver) {}
}
```

---

## Limitations
- **Syntax Tolerant**: The tool is a regex-based tokenizer and parser designed for documentation, not compiling. If a construct is complex or syntax-invalid, it preserves KDoc comments and prints the best possible declaration stub.
- **Top-Level Declarations**: Functions or properties declared outside of classes/objects are wrapped into a single wrapper class named after the filename with a `Kt` suffix (e.g., `Utils.kt` gets documented under `class UtilsKt`).

---

## Troubleshooting

### UTF-8 Encoding Issues on Windows
If Unicode characters (like Persian, Arabic, or Emoji comments) are garbled in Doxygen outputs:
1. Ensure your Kotlin files are saved in `UTF-8`.
2. Make sure your `Doxyfile` has `INPUT_ENCODING = UTF-8` (which is default).
3. The executable output stream is explicitly configured to write using `UTF-8` coding, preventing console encoding discrepancies.
