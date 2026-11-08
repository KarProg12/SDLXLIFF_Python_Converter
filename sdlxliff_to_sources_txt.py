import xml.etree.ElementTree as ET
from pathlib import Path
import tkinter as tk
from tkinter import filedialog


class SdlxliffExtractor:
    def __init__(self):
        self.file_path = None
        self.namespaces_map = {}

    def choose_file(self):
        """Responsible for:
            - displaying file choose window,
            - saving chosen file path"""
        # Create and hide the main tkinter window so it doesn't appear in the background
        root = tk.Tk()
        root.withdraw()

        # Open file choose window and save the file path to a variable
        chosen_file_path = filedialog.askopenfilename(
            title="Select file",
            filetypes=[("Wszystkie pliki", "*.*"), ("Pliki tekstowe", "*.txt")]
        )

        # If file was chosen
        if chosen_file_path:
            print(f"\nChosen file path: {chosen_file_path}")
            self.file_path = Path(chosen_file_path)
            return True
        # If file wasn't chosen
        else:
            print("File choose cancelled")
            return False

    def extract_sources(self):
        """All text tagged `source` to sources.txt extracting logic"""
        # Safety fuse: if no file was chosen stop the program
        if not self.file_path or not self.file_path.exists():
            print("\nNo valid file selected")
            return

        # XML parsing
        tree_xml = ET.parse(self.file_path)
        root_xml = tree_xml.getroot()


        # auto namespace fetching from file with root.tag
        # when splitting returns list ['{namespace', '}'] and index [0] deletes this curly bracket
        # strip separates and removes the curly bracket at the beginning of the namespace
        namespace = root_xml.tag.split('}')[0].strip('{')
        namespaces_map = {'xliff': namespace}

        # Saving to sources.txt file with memory cleaning
        with open('sources.txt', 'w', encoding='UTF-8') as txt_file:
            for element in root_xml.findall('.//xliff:source', namespaces_map):
                text = "".join(element.itertext()).strip()

                if text:
                    txt_file.write(text + "\n")

                element.clear()

        print("\nDone extracting")


if __name__ == '__main__':
    # Create an instance of class SdlxliffExtractor
    xliff_extractor = SdlxliffExtractor()

    # File choose method call
    # If user has chosen the file, start sources extraction
    if xliff_extractor.choose_file():
        xliff_extractor.extract_sources()
