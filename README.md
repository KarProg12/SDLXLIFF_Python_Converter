# SDLXLIFF Python Converter

A Python-based tool for processing SDLXLIFF translation files. The project focuses on extracting source segments, converting translation data into JSON, and making SDLXLIFF content easier to inspect and process.

## Overview

SDLXLIFF Python Converter is designed to simplify working with SDLXLIFF files used in computer-assisted translation (CAT) tools.

SDLXLIFF files are XML-based documents containing source text, target translations, and additional translation metadata. Their structure can make it difficult to access specific information manually.

This project aims to make that process easier by providing tools for parsing, extracting, and processing translation data.

## Features

- **SDLXLIFF parsing** – Reads SDLXLIFF files using Python's XML processing capabilities.
- **Source text extraction** – Extracts source segments from translation files.
- **JSON conversion** – Converts SDLXLIFF data into a structured JSON format.
- **Translation metadata** – Provides access to information stored alongside translation segments.
- **Segment filtering** – Supports filtering segments based on translation status and match information.
- **ZIP support** – Designed to work with SDLXLIFF files stored in ZIP archives.

## Project Structure

```text
SDLXLIFF_Python_Converter/
│
├── converter.py
├── transmAIte.py
├── xliff_dev_search_minitool.py
├── README.md
└── ...