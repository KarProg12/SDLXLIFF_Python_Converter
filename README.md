Extract source from .sdlxliff to .txt
What does it do?

This script reads a Trados translation file (.sdlxliff), extracts all source texts (`<source>`) and saves each one on a separate line in sources.txt.
How it works

    Load file — opens the .sdlxliff file as an XML document.
    Auto-detect namespace — extracts the XLIFF namespace URI (e.g. urn:oasis:names:tc:xliff:document:1.2) from the root <xliff> tag, so you don't have to hardcode it.
    Find segments — finds all <source> tags in the whole file.
    Extract text — collects plain text from each <source> tag, including text nested in Trados inline tags (e.g. <mrk>).
    Save to .txt — writes each non-empty text on a new line to sources.txt using utf-8 encoding.

## Files

    Input: program asks user to input filename or absolute path to file
    Output: sources.txt

## Requirements

    Python 3 only, no external dependencies. Uses the built-in xml.etree.ElementTree module.

## Usage

    python sdlxliff_to_sources_txt.py

