# SDLXLIFF Python Converter — Simple Version

A simple tool for translating SDLXLIFF files.

Workflow: **SDLXLIFF → JSON → 2x TXT → JSON → SDLXLIFF**

The original SDLXLIFF file is never modified. The tool exports segments to JSON, optionally to plain TXT files for easy editing, then writes the translations back into a new SDLXLIFF file.

## Features

- Export SDLXLIFF to JSON (only unlocked, untranslated segments)
- Import JSON back to SDLXLIFF
- JSON to 2 TXT files, and TXT back to JSON
- Inline tag support: tag name, attributes, tail text
- Safety checks: `.bak` backup, same-file block, skipped counter, tag count warning, TXT line count check

## Requirements

- Python 3.9+
- No external dependencies (standard library only: `json`, `xml.etree`, `os`, `shutil`)

## Functions

| Function | What it does |
| --- | --- |
| `eksportuj_do_json(plik_sdlxliff, folder_wyjsciowy)` | SDLXLIFF → `export.json` |
| `importuj_do_sdlxliff(plik_sdlxliff, plik_json, plik_wyjsciowy)` | JSON → new SDLXLIFF |
| `eksportuj_json_do_txt(plik_json, folder_wyjsciowy)` | JSON → 2 TXT files |
| `importuj_txt_do_json(plik_txt, plik_json)` | TXT → JSON |

## Usage

### 1. Export SDLXLIFF → JSON

```python
from converter import eksportuj_do_json

eksportuj_do_json("file.sdlxliff", "output")