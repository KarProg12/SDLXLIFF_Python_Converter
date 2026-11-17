SDLXLIFF Python Converter

A Python-based tool for processing SDLXLIFF translation files. The project focuses on extracting source segments, converting translation data into JSON, and making SDLXLIFF content easier to inspect and process.

Overview

SDLXLIFF Python Converter is designed to simplify working with SDLXLIFF files used in computer-assisted translation (CAT) tools.

SDLXLIFF files are XML-based documents containing source text, target translations, and additional translation metadata. Their structure can make it difficult to access specific information manually.

This project aims to make that process easier by providing tools for parsing, extracting, and processing translation data.

Features

- SDLXLIFF parsing – Reads SDLXLIFF files using Python's XML processing capabilities.
- Source text extraction – Extracts source segments from translation files.
- JSON conversion – Converts extracted SDLXLIFF data into a structured JSON format.
- Translation metadata – Provides access to information stored alongside translation segments.
- Segment filtering – Supports filtering segments based on their translation status and match information.
- ZIP support – Designed to work with SDLXLIFF files stored in ZIP archives.

Project Structure

SDLXLIFF_Python_Converter/
│
├── converter.py
├── transmAIte.py
├── xliff_dev_search_minitool.py
├── README.md
└── ...

Requirements

- Python 3.10 or newer
- Required Python packages (see the project's imports)

Installation

Clone the repository:

git clone https://github.com/KarProg12/SDLXLIFF_Python_Converter.git

Navigate to the project directory:

cd SDLXLIFF_Python_Converter

Install the required dependencies if necessary.

Usage

Run the appropriate Python script:

python converter.py

Provide an SDLXLIFF file as input and process its contents using the available functionality.

SDLXLIFF Format

SDLXLIFF (SDL XML Localization Interchange File Format) is an XML-based format used to store translation data.

A typical translation unit contains:

- Source – Original text.
- Target – Translated text.
- Translation status – Indicates the current state of a translation segment.
- Match information – Describes how closely a segment matches an existing translation memory entry.

Understanding this structure is essential for extracting and processing translation data correctly.

Technologies

- Python – Main programming language.
- XML / ElementTree – XML parsing and processing.
- JSON – Structured data representation.

Project Goals

The main goals of this project are:

- Simplifying SDLXLIFF file processing.
- Making translation segments easier to access.
- Providing structured output for further processing.
- Building a foundation for more advanced translation-related tools.

License

No license specified yet.