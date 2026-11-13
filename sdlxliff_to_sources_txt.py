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
        self.root_xml = None

    def get_ignored_segment_ids(self, trans_unit):
        """Returns a set of segment IDs (<mid>) that should be skipped."""
        ignored_statuses = {
            "Translated",
            "ApprovedTranslation",
            "ApprovedSignOff",
        }
        ignored_ids = set()

        sdl_segs = trans_unit.findall(".//sdl:seg-defs/sdl:seg", self.namespaces_map)
        # Iteration through every single segment in sdl-segs
        for seg in sdl_segs:
            seg_id = seg.get("id")  # Get value of attribute id
            status = seg.get("conf")  # Get translation status
            is_locked = seg.get("locked") == "true"  # If locked has value "true", return True, else False

            # If is_locked (like above) is true or fetched status is in ignored_statuses set
            if is_locked or (status in ignored_statuses):
                ignored_ids.add(seg_id)  # Add ignored segment id to the set of ignored_ids
                # (it's a set because set automatically removes duplicates (what's impossible with these ids because they're already unique. It's just to make sure))

        # Return set of ignored IDs
        return ignored_ids

    def choose_file(self):
        """Creates the initial GUI window with a start (SELECT FILE) button."""
        # Set up the main menu window size and title
        self.root = tk.Tk()
        self.root.title(f"Sdlxliff Extractor {self.version}")

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
                initialfile="source.txt",
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
        """Stream-based extraction of `seg-source` segments to sources.txt to keep RAM usage minimal."""
        # Safety check: ensure file exists
        if not self.file_path or not self.file_path.exists():
            print("\nNo valid file selected")
            return

        # Default namespaces map (XLIFF namespace will be updated dynamically from the root tag)
        self.namespaces_map = {
            'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
            'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
        }

        # Saved segments counter
        extracted_count = 0

        # Open the file on disk immediately to avoid RAM overload
        with open(self.output_path, 'w', encoding='UTF-8') as txt_file:
            # Stream-parse the XML file without loading the entire tree into RAM
            context = ET.iterparse(self.file_path, events=('start', 'end'))

            for event, elem in context:
                # Fetch the exact XLIFF namespace from the opening <xliff> tag
                if event == 'start' and elem.tag.endswith('xliff'):
                    if '}' in elem.tag:
                        self.namespaces_map['xliff'] = elem.tag.split('}')[0].replace('{', '')

                # Process each <trans-unit> block as soon as its closing tag </trans-unit> is reached
                elif event == 'end' and elem.tag.endswith('}trans-unit'):
                    if elem.get('translate') != 'no':
                        # Fetching segment IDs (<mid>) which should be ignored in this trans-unit
                        ignored_ids = self.get_ignored_segment_ids(elem)

                        seg_source = elem.find('xliff:seg-source', self.namespaces_map)
                        # If seg-source exists
                        if seg_source is not None:
                            # Iterate through every single segment <mrk mtype="seg">
                            for mrk in seg_source.findall('.//xliff:mrk[@mtype="seg"]', self.namespaces_map):
                                mid = mrk.get('mid')

                                # Skip only this exact segment if its ID is on the excluded list
                                if mid in ignored_ids:
                                    continue

                                text = ''.join(mrk.itertext()).strip().replace('\n', ' ').replace('\r', '')
                                if text:
                                    txt_file.write(text + '\n')
                                    extracted_count += 1
                        else:
                            # Protection for files that don't have <seg-source> yet, only <source>
                            source = elem.find('xliff:source', self.namespaces_map)
                            if source is not None:
                                text = ''.join(source.itertext()).strip().replace('\n', ' ').replace('\r', '')
                                if text:
                                    txt_file.write(text + '\n')
                                    extracted_count += 1

                    # Immediately free processed <trans-unit> from RAM
                    elem.clear()

        # --- Post-extraction checks (after file closure) ---
        if extracted_count == 0:
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
                f"Done extracting! File source.txt is ready.\n"
                f"Extracted segments: {extracted_count}\n"
                f"File absolute path: {self.output_path}"
            )

    def import_translated_sources(self):
        """Method that handles importing translated sources to targets by trans-unit mids (<mid>)"""
        pass

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