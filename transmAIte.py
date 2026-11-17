from converter import *
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
# [STRIPPED 75 bytes]
# Minimal GUI: file pickers, two actions, status line. No extra features.
# [STRIPPED 75 bytes]

root_window = tk.Tk()
root_window.title("SDLXLIFF <-> JSON")
root_window.geometry("640x545")

path_variables = {
    key: tk.StringVar()
    for key in ["export_source_path", "export_output_folder", "export_termbase_path",
                "import_source_path", "import_json_path", "import_output_path",
                "txt_json_path", "txt_output_folder_path", "txt_translate_path"]
}


def pick_path(variable, dialog_kind="file", file_types=None):
    # Opens a file / folder / save dialog and stores the chosen path in the field.
    chosen_path = {
        "file": lambda: filedialog.askopenfilename(filetypes=file_types or [("All files", "*.*")]),
        "dir": filedialog.askdirectory,
        "save": lambda: filedialog.asksaveasfilename(
            defaultextension=".sdlxliff",
            filetypes=[("SDLXLIFF", "*.sdlxliff"), ("All files", "*.*")]),
    }[dialog_kind]()
    if chosen_path:
        variable.set(chosen_path)


def add_row(parent_box, row_number, label_text, variable, browse_command):
    # One GUI row: label on the left, editable path in the middle, Browse button on the right.
    ttk.Label(parent_box, text=label_text).grid(row=row_number, column=0, sticky="w", pady=2)
    ttk.Entry(parent_box, textvariable=variable).grid(row=row_number, column=1, sticky="ew", padx=6, pady=2)
    ttk.Button(parent_box, text="Browse…", command=browse_command).grid(row=row_number, column=2, pady=2)
    parent_box.columnconfigure(1, weight=1)


def run_in_thread(function_to_run, success_message):
    # Runs work in a background thread, so the GUI never freezes during export/import.
    def thread_job():
        try:
            returned_message = function_to_run()
            final_message = returned_message if isinstance(returned_message, str) else success_message
            root_window.after(0, lambda: (status_text.set(final_message),
                                           messagebox.showinfo("Done", final_message)))
        except Exception as error:
            root_window.after(0, lambda: (status_text.set(f"ERROR: {error}"),
                                           messagebox.showerror("Error", str(error))))
    threading.Thread(target=thread_job, daemon=True).start()


def do_export():
    # Export button: checks required fields, loads the termbase if one was chosen, starts export.
    if not path_variables["export_source_path"].get() or not path_variables["export_output_folder"].get():
        return messagebox.showwarning("Missing data", "Select SDLXLIFF file and output folder.")
    def export_job():
        termbase_data = None
        if path_variables["export_termbase_path"].get():
            with open(path_variables["export_termbase_path"].get(), encoding="utf-8") as termbase_file:
                termbase_data = json.load(termbase_file)
        exported_count = export_sdlxliff_to_json(path_variables["export_source_path"].get(),
                                                 path_variables["export_output_folder"].get(), termbase_data)
        return f"Export finished. Exported {exported_count} segment(s)."
    run_in_thread(export_job, "Export finished.")


def do_import():
    # Import button: checks all three fields, starts import.
    if not all(path_variables[key].get() for key in ["import_source_path", "import_json_path", "import_output_path"]):
        return messagebox.showwarning("Missing data", "Select all 3 paths for import.")
    def import_job():
        inserted_count, skipped_count = import_to_sdlxliff(path_variables["import_source_path"].get(),
                                                           path_variables["import_json_path"].get(),
                                                           path_variables["import_output_path"].get())
        return f"Import finished. Inserted {inserted_count} segment(s), skipped {skipped_count}."
    run_in_thread(import_job, "Import finished.")


def do_txt_export():
    # JSON -> 2 TXT files button: checks JSON + output folder, starts TXT export.
    if not path_variables["txt_json_path"].get() or not path_variables["txt_output_folder_path"].get():
        return messagebox.showwarning("Missing data", "Select export.json and output folder for TXT.")
    def txt_export_job():
        segment_count = export_json_to_txt_files(path_variables["txt_json_path"].get(),
                                                 path_variables["txt_output_folder_path"].get())
        return f"TXT export finished. Exported {segment_count} segment(s) to 2 TXT files."
    run_in_thread(txt_export_job, "TXT export finished.")


def do_txt_import():
    # TXT -> JSON button: checks TXT file + JSON to update, starts TXT import.
    if not path_variables["txt_translate_path"].get() or not path_variables["txt_json_path"].get():
        return messagebox.showwarning("Missing data", "Select the edited TXT file and the export.json to update.")
    def txt_import_job():
        updated_count = import_txt_files_to_json(path_variables["txt_translate_path"].get(),
                                                 path_variables["txt_json_path"].get())
        return f"TXT -> JSON finished. Updated {updated_count} segment(s)."
    run_in_thread(txt_import_job, "TXT -> JSON finished.")


# Export section: SDLXLIFF file, output folder, optional termbase, Export button.
export_box = ttk.LabelFrame(root_window, text=" Export SDLXLIFF -> JSON ", padding=8)
export_box.pack(fill="x", padx=10, pady=(10, 5))

add_row(export_box, 0, "SDLXLIFF file:", path_variables["export_source_path"],
        lambda: pick_path(path_variables["export_source_path"], "file",
                          [("SDLXLIFF", "*.sdlxliff"), ("All files", "*.*")]))

add_row(export_box, 1, "Output folder:", path_variables["export_output_folder"],
        lambda: pick_path(path_variables["export_output_folder"], "dir"))

add_row(export_box, 2, "Termbase (optional):", path_variables["export_termbase_path"],
        lambda: pick_path(path_variables["export_termbase_path"], "file",
                          [("JSON", "*.json"), ("All files", "*.*")]))

ttk.Button(export_box, text="Export to JSON", command=do_export).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))

# TXT section: JSON <-> 2 TXT files.
txt_box = ttk.LabelFrame(root_window, text=" TXT: JSON <-> 2 TXT files ", padding=8)
txt_box.pack(fill="x", padx=10, pady=5)

add_row(txt_box, 0, "export.json:", path_variables["txt_json_path"],
        lambda: pick_path(path_variables["txt_json_path"], "file", [("JSON", "*.json"), ("All files", "*.*")]))

add_row(txt_box, 1, "TXT output folder:", path_variables["txt_output_folder_path"],
        lambda: pick_path(path_variables["txt_output_folder_path"], "dir"))

add_row(txt_box, 2, "TXT to import: \n(default filename is export_translate)", path_variables["txt_translate_path"],
        lambda: pick_path(path_variables["txt_translate_path"], "file", [("Text", "*.txt"), ("All files", "*.*")]))

ttk.Button(txt_box, text="JSON -> 2 TXT files", command=do_txt_export).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
ttk.Button(txt_box, text="TXT -> JSON", command=do_txt_import).grid(row=3, column=2, sticky="ew", pady=(6, 0))

# Import section: original SDLXLIFF, translated JSON, save-as path, Import button.
import_box = ttk.LabelFrame(root_window, text=" Import JSON -> SDLXLIFF ", padding=8)
import_box.pack(fill="x", padx=10, pady=5)

add_row(import_box, 0, "Original SDLXLIFF:", path_variables["import_source_path"],
        lambda: pick_path(path_variables["import_source_path"], "file",
                          [("SDLXLIFF", "*.sdlxliff"), ("All files", "*.*")]))

add_row(import_box, 1, "Translated JSON:", path_variables["import_json_path"],
        lambda: pick_path(path_variables["import_json_path"], "file",
                          [("JSON", "*.json"), ("All files", "*.*")]))

add_row(import_box, 2, "Save as:", path_variables["import_output_path"],
        lambda: pick_path(path_variables["import_output_path"], "save"))

ttk.Button(import_box, text="Import to SDLXLIFF", command=do_import).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))

# Status line at the bottom of the window.
status_text = tk.StringVar(value="Ready.")

ttk.Label(root_window, textvariable=status_text).pack(anchor="w", padx=12, pady=8)

root_window.mainloop()