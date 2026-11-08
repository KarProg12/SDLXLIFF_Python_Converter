# SDLXLIFF Source Text Extractor

A lightweight Python desktop application designed to parse localization files (`.sdlxliff`, `.xliff`, `.xml`) and extract all raw source text segments into a single plain text file.

## Features
* **XML/XLIFF Parsing:** Automatically extracts text from `<source>` tags while dynamically handling XML namespaces.
* **Memory Efficient:** Clears processed XML nodes during iteration to optimize RAM usage.
* **User-Friendly GUI:** Simple desktop interface powered by `tkinter` for seamless file selection and output path configuration.
* **UTF-8 Support:** Ensures proper encoding preservation for multi-language localization workflows.

## Technical Stack
* **Language:** Python 3.x
* **GUI Framework:** `tkinter` (built-in)
* **XML Parser:** `xml.etree.ElementTree` (built-in)
* **File System Operations:** `pathlib` (built-in)

## How It Works
1. Launching the script opens a GUI window prompting the user to select an input file (`.sdlxliff`, `.xliff`, or `.xml`).
2. The user specifies the destination `.txt` file path.
3. The application parses the XML tree, dynamically fetches the root namespace, extracts text from all `<source>` elements, and saves them line-by-line.
