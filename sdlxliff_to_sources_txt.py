import xml.etree.ElementTree as ET
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os


class SdlxliffExtractor:
    def __init__(self):
        # Initialize paths and variables
        self.file_path = None
        self.output_path = None
        self.namespaces_map = {}
        self.version = 'v1.1'

    def ignore_translated_statuses(self, trans_unit, namespaces_map):
        # If the status of attribute translate is 'no' ignore the element
        if trans_unit.get('translate') == 'no':
            return True

        # Set of ignored statuses
        ignored_statuses = {"Translated", "ApprovedTranslation", "ApprovedSignOff"}

        # Search whole doc and return all text or data segments marked with tag 'sdl:seg'
        # './/' means it searches everywhere, in parents and in children etc.
        sdl_segs = trans_unit.findall('.//sdl:seg', namespaces_map)

        # For every single segment in all file segments
        for seg in sdl_segs:
            # Translation status (e.g. 'Translated', 'ApprovedTranslation' or 'ApprovedSignOff')
            status = seg.get('conf')
            # Accessibility
            is_locked = seg.get('locked') == 'true'

            # If one of those 2 tags above is return True
            # This expression is the same as this:
            # if is_locked or (status in ignored_statuses) == True:
            if is_locked or (status in ignored_statuses):
                return True

        # If none of those above will be executed, return False
        return False

    def choose_file(self):
        """Creates the initial GUI window with a start (SELECT FILE) button."""
        # Set up the main menu window size and title
        self.root = tk.Tk()
        self.root.title(f"Sdlxliff to txt sources extractor {self.version}")

        # Instruction text for supported formats
        label = ttk.Label(self.root, text="Supported file extensions: .xml/.xliff/.sdlxliff\n\n"
                                         "Click the button to select a file, you want to extract source texts:")
        label.pack(pady=15)

        # Button to open file explorer
        btn = ttk.Button(self.root, text="SELECT FILE", command=self._on_button_click)
        btn.pack()

        # Run Tkinter main loop (stops script execution here until window closes)
        self.root.mainloop()

        # Returns True only if a valid input path was stored
        return bool(self.file_path)

    def _on_button_click(self):
        """Handles source file selection and destination path choice."""
        # Open dialog to pick the input file
        chosen_file_path = filedialog.askopenfilename(
            title="Select file",
            filetypes=[("All files", "*.*"), ("Text files", "*.txt")]
        )

        # Trigger save dialog only if input file was successfully selected
        if chosen_file_path:
            chosen_output_path = filedialog.asksaveasfilename(
                title="Where to save the output file?",
                initialfile="sources.txt",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )

            # Proceed if user confirmed the output path
            if chosen_output_path:
                print(f"\nChosen file path: {chosen_file_path}")
                print(f"Output file path: {chosen_output_path}")

                # Convert raw paths to Path objects
                self.file_path = Path(chosen_file_path)
                self.output_path = Path(chosen_output_path)

                self.root.quit()
                # Close menu window to pass execution to extraction phase
                self.root.destroy()
            else:
                print("Saving cancelled")
        else:
            print("File choose cancelled")
            messagebox.showwarning("Cancelled", "No file selected.")

    def extract_sources(self):
        """All text tagged `source` to sources.txt extracting logic"""
        # Safety check: ensure file exists
        if not self.file_path or not self.file_path.exists():
            print("\nNo valid file selected")
            return

        # Parse XML structure
        tree_xml = ET.parse(self.file_path)
        root_xml = tree_xml.getroot()

        # Safe fetching of XLIFF namespaces from root
        # Gets rid of curly braces around the full root name
        namespace = ""
        if '}' in root_xml.tag:
            namespace = root_xml.tag.split('}')[0].replace('{', '')

        # Namespaces dict (XLIFF and SDL's metadata for the statuses)
        namespaces_map = {
            'xliff': namespace,
            'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
        }

        # Saved segments counter
        extracted_count = 0

        # Open the file on disk immediately to avoid RAM overload
        with open(self.output_path, 'w', encoding='UTF-8') as txt_file:
            # All elements tagged 'trans-unit' in list
            all_trans_units = root_xml.findall('.//xliff:trans-unit', namespaces_map)

            for trans_unit in all_trans_units:
                if self.ignore_translated_statuses(trans_unit, namespaces_map):
                    continue

                element = trans_unit.find('xliff:source', namespaces_map)
                if element is not None:
                    text = "".join(element.itertext()).strip()

                    if text:
                        txt_file.write(text + '\n')
                        extracted_count += 1

        # --- KEY MOMENT (After file closure) ---
        if extracted_count == 0:
            # If extracted counter value is 0 remove created file from disk
            if self.output_path.exists():
                os.remove(self.output_path)

            print("\nNo segments found to translate.")
            messagebox.showwarning(
                "No content to extract",
                "No segments were found for translation in the selected file!\n"
                "(All segments are already translated, locked, or the file is empty.)\n\n"
                "Output file not created."
            )
        else:
            print(f"\nDone extracting. Extracted segments: {extracted_count}")
            messagebox.showinfo(
                "Success",
                f"Done extracting! File sources.txt is ready.\n"
                f"Extracted segments: {extracted_count}\n"
                f"File absolute path: {self.output_path}"
            )


if __name__ == '__main__':
    # Initialize the extractor instance
    xliff_extractor = SdlxliffExtractor()

    while True:
        # Reset the file before choice
        xliff_extractor.file_path = None

        # If user clicks 'X' button in window or press 'Cancel' quit the loop
        if not xliff_extractor.choose_file():
            print("\nProgram closed by user.")
            break

        # Extraction activation
        xliff_extractor.extract_sources()