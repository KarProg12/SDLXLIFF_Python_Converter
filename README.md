# SDLXLIFF Python Converter

A minimal GUI tool for translating SDLXLIFF files.

Workflow: **SDLXLIFF → JSON → TXT → JSON → SDLXLIFF**

The original SDLXLIFF file is never modified. The tool exports segments to JSON, optionally to plain TXT files for easy editing, then writes the translations back into a new SDLXLIFF file.

## Features

- Export SDLXLIFF to JSON (only unlocked, untranslated segments)
- Import JSON back to SDLXLIFF
- JSON to 2 TXT files, and TXT back to JSON
- Full inline tag support: tag name, all attributes, namespace, tail text
- Segment counts in every messagebox: exported / inserted / skipped / updated
- Optional termbase filtering (only terms that occur in the source text)
- Streaming export with `iterparse` — large files do not load fully into memory

## Requirements

- Python 3.9+
- No external dependencies (standard library only: `tkinter`, `xml.etree`, `json`)

## Run

```bash
python transmAIte.py
```

## Usage

The window has three sections, top to bottom, in workflow order.

### 1. Export SDLXLIFF → JSON

| Field | Description |
| --- | --- |
| SDLXLIFF file | Source file from Trados |
| Output folder | Folder for `export.json` |
| Termbase (optional) | JSON termbase: `{"required": {...}, "forbidden": [...]}` |

Click **Export to JSON**.

Result: `Export finished. Exported N segment(s).`

### 2. TXT: JSON ↔ 2 TXT files

| Field | Description |
| --- | --- |
| export.json | File from step 1 |
| TXT output folder | Folder for the TXT files |
| TXT to import | Edited TXT file, for the way back |

Click **JSON → 2 TXT files**. Two files are created:

- `export_source.txt` — read-only, source text only
- `export_translate.txt` — edit this file

Each segment is one block:

```text

[ID: 1|1]
SOURCE: Hello <g id="1">world</g>
TRANSLATION:
Witaj <g id="1">swiecie</g>
```

Rules for editing:

- Write the translation under `TRANSLATION:`, do not replace that line
- Do not delete the `[ID: trans-unit|seg]` line — it is the return address
- Copy inline tags (`<g ...>...</g>`) exactly, do not translate them

Then click **TXT -> JSON**.

Result: `TXT -> JSON finished. Updated N segment(s).`

Only `ai_translation` is changed in the JSON. Everything else stays untouched.

### 3. Import JSON → SDLXLIFF

| Field | Description |
| --- | --- |
| Original SDLXLIFF | The same, unmodified file from step 1 |
| Translated JSON | `export.json` after translation |
| Save as | New SDLXLIFF file, e.g. `file_translated.sdlxliff` |

Click **Import to SDLXLIFF**.

Result: `Import finished. Inserted N segment(s), skipped M.`

Imported segments get status `Draft`. Open the new file in Trados.

## JSON format

One segment in `export.json`:

```json
{
  "trans-unit_id": "1",
  "seg_id": "1",
  "status": "Not Translated",
  "source": "Hello <g id=\"1\">world</g>",
  "target": "",
  "ai_translation": "Witaj <g id=\"1\">swiecie</g>",
  "ai_comment": ""
}
```

Import reads only `ai_translation`. `source`, `trans-unit_id` and `seg_id` must not be changed.

## Troubleshooting

| Message | Meaning | Fix |
| --- | --- | --- |
| `Exported 0` | Nothing to translate | File is already translated, or all segments are locked |
| `Updated 0` | Nothing written in TXT | Write text under `TRANSLATION:`, keep `[ID:]` lines |
| `Inserted 0` | No translations in JSON | Fill `ai_translation`, not `target`, then import the translated JSON |
| `Skipped N` | N translations have no matching ID in the SDLXLIFF | Check that the JSON belongs to this SDLXLIFF file |

## Project structure

```text
SDLXLIFF_Python_Converter/
├── transmAIte.py   # Main app: SDLXLIFF <-> JSON <-> TXT
├── converter.py    # Legacy converter
├── transmAIte_icon.ico
└── README.md
```