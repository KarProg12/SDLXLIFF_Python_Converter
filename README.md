# TransMAiTE — SDLXLIFF ↔ JSON / TXT Converter

A desktop application written in Python that facilitates the translation of **SDLXLIFF** files (used, amongst other things, in Trados Studio) using AI models
(LLMs) or external text tools. The programme extracts untranslated segments along with their XML tags, converts them into convenient intermediate formats
(**JSON** and pairs of **TXT** files), and then safely injects the finished translations back into the `.sdlxliff` file structure.

## ✨ Key features

- **Smart SDLXLIFF → JSON export (`export_to_json`):**

    - Filters segments — exports only those that are untranslated and unlocked (skips the statuses `Translated`, `ApprovedTranslation`, `ApprovedSignOff` and
segments with the attribute `locked="true"`).

    - Preserves identifiers (`trans-unit_id`, `seg_id`), existing working translations and internal XML formatting tags (e.g. `<g>`, `<x/>`).

    - Processes the file in-stream (`ET.iterparse`), which reduces memory usage with large files.

- **Two-way conversion between JSON and 2x TXT (`export_json_to_txt`, `import_txt_to_json`):**

    - Generates two line-synchronised files: `source.txt` (read-only) and `target.txt` (for translation).

    - `target.txt` starts empty on purpose — you fill it from scratch, one line per segment.

    - Replaces internal newline characters with the sequence `\n`, ensuring a **1 line = 1 segment** layout.

    - During import, it checks that the number of lines in the TXT file matches the number of segments in the JSON file and reports statistics (changed by user,
unchanged, empty).

    - Trailing empty lines at the end of the TXT file are ignored, so an extra Enter at the end does not break the import.

- **Safe JSON → SDLXLIFF import (`import_to_sdlxliff`):**

    - Creates an automatic backup of the source file with the `.bak` extension.

    - Prevents the original input file from being accidentally overwritten.

    - Verifies the number of tags (`<`) between the source and translation and issues a warning in the console in the event of discrepancies.

    - Reconstructs the XML namespaces required by Trados (`xliff` / `sdl`) and sets the status of imported segments to `Draft`.

    - Counts only segments that were really changed by the user (compares old and new text before saving).

- **Simple graphical user interface (GUI):**

    - Built with **`ttk`** (built into Python) — dark mode interface, divided into three working sections, with file/folder selection windows and a status bar at the bottom of the screen.
    - Large, readable layout, designed for comfortable everyday use.

## 🛠️ Technologies

The project is based entirely on the **Python 3 standard library** — it does not require the installation of any external packages (`pip`):

- `tkinter` + `ttk` (`filedialog`, `messagebox`) — the application’s graphical user interface

- `xml.etree.ElementTree` — parsing, tag reconstruction and saving of SDLXLIFF files

- `json` — handling of the intermediate data format `export.json`

- `os`, `shutil` — path management, creating directories and `.bak` backups

## 📂 Repository structure

- `transmAIte.py` — the main executable file containing the graphical user interface (`ttk`) as well as event handling and error messages.

- `converter.py` — the business logic layer responsible for XML parsing, namespace handling and conversion between the `.sdlxliff`, `.json` and `.txt` formats.

## 🚀 Download

No Python or installation is needed to use the programme.

Download the latest ready-to-use version here:

**https://github.com/KarProg12/TransMAiTE/releases**

Download `TransmAIte.exe` from the latest release and run it — that is all.

## 📖 Step-by-step guide (Workflow)

1. **Export segments from SDLXLIFF:**

      - In the **Export SDLXLIFF -> JSON** section, select the `.sdlxliff` file and the output folder.

      - Click **Export to JSON** to create the `export.json` file.

2. **Translation (choose one of the following options):**

      - **TXT path (convenient for AI / editors):** In the **TXT: JSON <-> 2 TXT files** section, specify the `export.json` file and the destination folder, then
click **JSON -> 2 TXT files**. Translate the contents of the `target.txt` file (ensuring you retain exactly the same number of lines and XML tags, e.g.
`<g id="1">...</g>`), then import it back using the **TXT -> JSON** button.

      - **JSON path:** Enter the values for the `"target"` key directly in the `export.json` file.

3. **Saving the finished SDLXLIFF file:**

      - In the **Import JSON -> SDLXLIFF** section, select the original `.sdlxliff` file, the updated `export.json` file and a new name/path for the output file.

      - Click **Import to SDLXLIFF**. The resulting file is ready to be opened and verified in a CAT tool (e.g. Trados Studio).

## ⚠️ Important tips

- **Do not delete or change the line numbers** in the `target.txt` file — the programme matches translations to segments based on the line number.

- `target.txt` is exported empty on purpose. Fill every line, even if you leave a segment untranslated — leave it as an empty line, do not delete it.

- An extra empty line at the very end of `target.txt` is ignored and does not break the import.

- **Retain the XML tags** visible in the source segment (e.g. `<g id="1">text</g>`) to avoid structural errors in Trados Studio.

- The output `.sdlxliff` file must have a different name or location to the input file.