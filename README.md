# TransmAIte — SDLXLIFF ↔ JSON / TXT Converter

A desktop application written in Python that facilitates the translation of **SDLXLIFF** files (used, amongst other things, in Trados Studio) using AI models (LLMs) or external text tools. The programme extracts untranslated segments along with their XML tags, converts them into convenient intermediate formats (**JSON** and pairs of **TXT** files), and then safely injects the finished translations back into the `.sdlxliff` file structure.

## ✨ Key features

* **Smart SDLXLIFF → JSON export (`export_to_json`):**
  * Filters segments — exports only those that are untranslated and unlocked (skips the statuses `Translated`, `ApprovedTranslation`, `ApprovedSignOff` and segments with the attribute `locked="true"`).
  * Preserves identifiers (`trans-unit_id`, `seg_id`), existing working translations and internal XML formatting tags (e.g. `<g>`, `<x/>`).
  * Processes the file in-stream (`ET.iterparse`), which reduces memory usage with large files.
* **Two-way conversion between JSON and 2x TXT (`export_json_to_txt`, `import_txt_to_json`):**
  * Generates two line-synchronised files: `export_source.txt` (read-only) and `export_target.txt` (for translation).
  * Replaces internal newline characters with the sequence `\n`, ensuring a **1 line = 1 segment** layout.
  * During import, it checks that the number of lines in the TXT file matches the number of segments in the JSON file and reports statistics (changed, unchanged, empty).
* **Safe JSON → SDLXLIFF import (`import_to_sdlxliff`):**
  * Creates an automatic backup of the source file with the `.bak` extension.
  * Prevents the original input file from being accidentally overwritten.
  * Verifies the number of tags (`<`) between the source and translation and issues a warning in the console in the event of discrepancies.
  * Reconstructs the XML namespaces required by Trados (`xliff` / `sdl`) and sets the status of imported segments to `Draft`.
* **Simple graphical user interface (GUI):**
  * An intuitive window divided into three working sections, with file/folder selection windows and a status bar at the bottom of the screen.

## 🛠️ Technologies

The project is based entirely on the **Python 3 standard library** — it does not require the installation of any external packages (`pip`):

* `tkinter` (`filedialog`, `messagebox`, `ttk`) — the application’s graphical user interface
* `xml.etree.ElementTree` — parsing, tag reconstruction and saving of SDLXLIFF files
* `json` — handling of the intermediate data format `export.json`
* `os`, `shutil` — path management, creating directories and `.bak` backups

## 📂 Repository structure

* `transmAIte.py` — the main executable file containing the graphical user interface (`tkinter`) as well as event handling and error messages.
* `converter.py` — the business logic layer responsible for XML parsing, namespace handling and conversion between the `.sdlxliff`, `.json` and `.txt` formats.

## 🚀 Installation and setup

1. **Ensure you have Python 3 installed** (along with the `tkinter` module, which is included by default in installers for Windows and macOS).
2. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd SDLXLIFF_Python_Converter
   ```
3. **Run the programme:**
   ```bash
   python transmAIte.py
   ```

## 📖 Step-by-step guide (Workflow)

1. **Export segments from SDLXLIFF:**
   * In the **Export SDLXLIFF -> JSON** section, select the `.sdlxliff` file and the output folder.
   * Click **Export to JSON** to create the `export.json` file.
2. **Translation (choose one of the following options):**
   * **TXT path (convenient for AI / editors):** In the **TXT: JSON <-> 2 TXT files** section, specify the `export.json` file and the destination folder, then click **JSON -> 2 TXT files**. Translate the contents of the `export_target.txt` file (ensuring you retain exactly the same number of lines and XML tags, e.g. `<g id="1">...</g>`), then import it back using the **TXT -> JSON** button.
   * **JSON path:** Enter the values for the `"target"` key directly in the `export.json` file.
3. **Saving the finished SDLXLIFF file:**
   * In the **Import JSON -> SDLXLIFF** section, select the original `.sdlxliff` file, the updated `export.json` file and a new name/path for the output file.
   * Click **Import to SDLXLIFF**. The resulting file is ready to be opened and verified in a CAT tool (e.g. Trados Studio).

## ⚠️ Important tips

* **Do not delete or change the line numbers** in the `*_target.txt` file — the programme matches translations to segments based on the line number.
* **Retain the XML tags** visible in the source segment (e.g. `<g id="1">text</g>`) to avoid structural errors in Trados Studio.
* The output `.sdlxliff` file must have a different name or location to the input file.


Przetłumaczono za pomocą DeepL (https://dee.pl/apps)