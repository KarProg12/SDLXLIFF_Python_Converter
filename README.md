# TransMAiTE

### SDLXLIFF ↔ JSON / TXT Converter

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-tkinter%20%2F%20ttk-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Download-Releases-orange.svg)](https://github.com/KarProg12/TransMAiTE/releases)

TransMAiTE is a desktop application that simplifies the translation of **SDLXLIFF** files (used in Trados Studio and other CAT tools) with the help of AI models (LLMs) or external text editors.

It extracts untranslated segments — together with their XML tags — into convenient intermediate formats (**JSON** and **TXT**), and then safely injects the finished translations back into the `.sdlxliff` structure.

No Python installation or external packages are required to use the released `.exe` version.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Important Notes](#important-notes)
- [Backup & Recovery](#backup--recovery)
- [License](#license)

---

## Features

### Export — SDLXLIFF → JSON + TXT

One click (`export_to_json_and_txts`) creates a complete project folder containing:

- `export.json` — structured list of segments
- `source.txt` — source texts, one segment per line
- `target.txt` — empty file, ready for translation

Export rules:

- Only untranslated and unlocked segments are exported
- Skipped statuses: `Translated`, `ApprovedTranslation`, `ApprovedSignOff`
- Skipped segments with `locked="true"`
- Preserved data: `trans-unit_id`, `seg_id`, existing working translations, internal XML formatting tags (e.g. `<g>`, `<x/>`)
- Memory-efficient streaming with `ET.iterparse`

### Import — TXT → JSON → SDLXLIFF

One click (`import_txt_to_sdlxliff`) performs the full import chain:

1. Imports the translated `target.txt` back into `export.json`
2. Inserts translations from `export.json` into the `.sdlxliff` file

Import rules:

- Validates that the number of TXT lines matches the number of JSON segments
- Trailing empty lines at the end of the TXT file are ignored
- Empty lines in the middle are preserved, so line-to-segment mapping stays correct
- Internal newlines are stored as `\n`, preserving the **1 line = 1 segment** layout
- Warns in the console when the number of tags (`<`) differs between source and translation
- Rebuilds XML namespaces required by Trados (`xliff` / `sdl`)
- Sets imported segments to `Draft`
- Console log reports how many segments were actually changed by the user; the GUI reports how many translations were inserted

### Graphical Interface

- Built with **`ttk`** (Python standard library, no extra dependencies)
- Dark mode interface with a status bar
- Two sections only: **Export** and **Import** — no separate TXT → JSON section
- After selecting the first `.sdlxliff` file, the application auto-fills:
    - Output / project folder
    - Original file in the Import section
    - `export.json` path
- The user still selects manually:
    - Translated `target.txt`
    - Output file (`Save as`)

---

## How It Works

```text
.sdlxliff
    ↓  Export
export.json + source.txt + target.txt (empty)
    ↓  Translate target.txt / edit export.json
export.json (with translations)
    ↓  Import
translated .sdlxliff