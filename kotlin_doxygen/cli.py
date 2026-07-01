import sys
import os
from kotlin_doxygen import __version__
from kotlin_doxygen.filter import filter_kotlin

def print_usage():
    usage = """Kotlin Doxygen Filter/Generator

Usage:
  kotlin-doxygen <file_path>    Process a Kotlin file and print Doxygen-compatible output to stdout.
  kotlin-doxygen --help, -h     Show this help message.
  kotlin-doxygen --version, -v  Show the tool version.
"""
    sys.stderr.write(usage)

def main():
    # Reconfigure sys.stdout and sys.stderr to write UTF-8 safely
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    arg = sys.argv[1]
    if arg in ('--help', '-h'):
        print_usage()
        sys.exit(0)
    elif arg in ('--version', '-v'):
        sys.stdout.write(f"kotlin-doxygen version {__version__}\n")
        sys.exit(0)
    else:
        # File parsing mode
        if not os.path.exists(arg):
            sys.stderr.write(f"Error: File '{arg}' not found.\n")
            sys.exit(1)
        if not os.path.isfile(arg):
            sys.stderr.write(f"Error: Path '{arg}' is not a file.\n")
            sys.exit(1)

        try:
            with open(arg, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            filename = os.path.basename(arg)
            result = filter_kotlin(content, filename)
            sys.stdout.write(result)
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"Error: Failed to process file '{arg}': {e}\n")
            sys.exit(1)
