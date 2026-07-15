# AGENTS.md

This file contains instructions for AI agents working on this codebase.

## Project Overview

A Kotlin-to-Java syntax filter for Doxygen. Converts Kotlin source files into pseudo-Java that Doxygen can parse, enabling documentation generation for Kotlin projects.

## Architecture

```
kotlin_doxygen/
├── cli.py          # Entry point, handles file I/O and CLI args
├── parser.py       # Tokenizer and token stream
├── renderer.py     # Type mapping, inference, parameter translation
├── filter.py       # Main transformation logic (declaration parsing)
└── __init__.py     # Version
```

### Data Flow
```
Kotlin source → TokenStream → filter_kotlin() → Java-like pseudo-code → Doxygen
```

## Key Concepts

### Token Types
- `IDENTIFIER` - keywords, names
- `OPERATOR` - `<`, `>`, `==`, `->`, etc.
- `SYMBOL` - `{`, `}`, `(`, `)`, `:`, etc.
- `STRING`, `CHAR`, `DOC_COMMENT`, etc.

### Scope Tracking
`scope_stack` tracks nested class/object/companion scopes. Each entry has:
- `type`: 'class', 'object', 'companion'
- `is_object`: bool
- `is_sealed`: bool
- `brace_depth`: int
- `name`: str

### Type Mapping
- `TYPE_MAP` - simple type conversions (Int→int, String→String)
- `GENERIC_TYPE_MAP` - generic wrapper types (MutableList→List)
- `BOXED_TYPE_MAP` - boxed types for generics (Int→Integer)

## Common Tasks

### Adding a new Kotlin syntax pattern
1. Identify the token pattern in `filter.py`
2. Add parsing logic in the appropriate section
3. Add type mapping in `renderer.py` if needed
4. Add tests in `tests/test_real_world.py`

### Adding a new type mapping
1. Add to `TYPE_MAP` for simple types
2. Add to `GENERIC_TYPE_MAP` for generic types
3. Add to `BOXED_TYPE_MAP` if needed for generic contexts

### Testing
```bash
# Run all tests
python -m unittest tests.test_cli tests.test_real_world -v

# Run specific test file
python -m unittest tests.test_cli -v

# Test a Kotlin file
python -m kotlin_doxygen path/to/file.kt

# Test with Doxygen
python -m kotlin_doxygen file.kt > filtered.java
doxygen Doxyfile
```

## Known Limitations

1. **No full Kotlin parser** - uses heuristic token walking
2. **Type inference** - falls back to `Object` for complex expressions
3. **Function types** - mapped to `Function` (Doxygen limitation)
4. **Context receivers** - handled as static methods
5. **Sealed class subtypes** - not marked as `static` (correct for Kotlin)

## Doxygen Integration

Use `FILTER_PATTERNS` in Doxyfile:
```
FILTER_PATTERNS = kt=kotlin-doxygen
EXTENSION_MAPPING = kt=Java
```

Or pre-filter:
```bash
python -m kotlin_doxygen input.kt > output.java
```

## Commit Style

Use conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `test:` adding tests
- `docs:` documentation
- `refactor:` code refactoring

## Versioning

Follow semver:
- `v0.1.x` - initial implementation
- `v0.2.x` - improved type inference, coroutine support, sealed classes
- `v0.3.x` - future improvements
