import xml.etree.ElementTree as ET
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


class SdlxliffExtractor():
    def __init__(self):
        # Initialize paths and variables
        self.file_path = None
        self.output_path = None
        self.namespaces_map = {}

    def choose_file(self):
        """Creates the initial GUI window with a start button."""
        # Set up the main menu window size and title
        self.root = tk.Tk()
        self.root.title("Sdlxliff to txt sources extractor v1.0")
        self.root.geometry("350x130")

        # Instruction text for supported formats
        label = tk.Label(self.root, text="Supported file extensions: .xml/.xliff/.sdlxliff\n\n"
                                         "Click the button to select a file, you want to extract source texts:")
        label.pack(pady=15)

        # Button to open file explorer
        btn = tk.Button(self.root, text="SELECT FILE", command=self._on_button_click)
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
            filetypes=[("Wszystkie pliki", "*.*"), ("Pliki tekstowe", "*.txt")]
        )

        # Trigger save dialog only if input file was successfully selected
        if chosen_file_path:
            chosen_output_path = filedialog.asksaveasfilename(
                title="Where to save the output file?",
                initialfile="sources.txt",
                defaultextension=".txt",
                filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
            )

            # Proceed if user confirmed the output path
            if chosen_output_path:
                print(f"\nChosen file path: {chosen_file_path}")
                print(f"Output file path: {chosen_output_path}")

                # Convert raw paths to Path objects
                self.file_path = Path(chosen_file_path)
                self.output_path = Path(chosen_output_path)

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

        # Auto namespace fetching from file root tag
        namespace = root_xml.tag.split('}')[0].strip('{')
        namespaces_map = {'xliff': namespace}

        # Open chosen destination file with UTF-8 encoding
        with open(self.output_path, 'w', encoding='UTF-8') as txt_file:
            # Find and process all source elements matching namespace
            for element in root_xml.findall('.//xliff:source', namespaces_map):
                text = "".join(element.itertext()).strip()

                # Write to file only if segment contains actual text
                if text:
                    txt_file.write(text + "\n")

                # Free up RAM by clearing the processed XML node
                element.clear()

        print("\nDone extracting")
        # Visual success pop-up message in GUI
        messagebox.showinfo("Success", f"Done extracting! File sources.txt is ready.\n"
                                       f"File absolute path: {self.output_path}")


if __name__ == '__main__':
    # Initialize the extractor instance
    xliff_extractor = SdlxliffExtractor()

    # Trigger file selection and start extraction if successful
    if xliff_extractor.choose_file():
        xliff_extractor.extract_sources()