# Uproszczone GUI - CustomTkinter
# pip install customtkinter

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk

from converter import Converter as Cnv

converter = Cnv()

# Kolory z ikony aplikacji: ciemne tlo + zielen z ikony
BG_DARK = "#232323"
CARD_DARK = "#2E2E2E"
BORDER_DARK = "#3A3A3A"
GREEN_DARK = "#18863F"
GREEN_MAIN = "#5ABC6F"
GREEN_LIGHT = "#2A3D30"

ctk.set_appearance_mode("dark")  # tryb ciemny na stale

window = ctk.CTk()
window.title("TransmAIte (SDLXLIFF <- 2x TXT -> JSON)")
window.geometry("680x755")
window.configure(fg_color=BG_DARK)

# Gorny pasek
top = ctk.CTkFrame(window, fg_color=GREEN_DARK, corner_radius=0, height=52)
top.pack(fill="x")
top.pack_propagate(False)
ctk.CTkLabel(top, text="  TransmAIte", text_color="white", font=("Segoe UI", 17, "bold")).pack(side="left")
ctk.CTkLabel(top, text="SDLXLIFF  <->  TXT  <->  JSON  ", text_color="#D6F5DD", font=("Segoe UI", 10)).pack(side="right", padx=12)

# Sciezki - jedna petla, tak jak bylo wczesniej, bo to tu jest czytelniejsze
paths = {}
for path_key in ["export_file", "export_folder",
                 "import_file", "import_json", "import_save",
                 "txt_json", "txt_folder", "txt_to_import"]:
    paths[path_key] = tk.StringVar()

status = tk.StringVar(value="Ready.")


def choose_path(path_variable, choice_type):
    chosen = ""
    if choice_type == "file":
        chosen = filedialog.askopenfilename()
    elif choice_type == "folder":
        chosen = filedialog.askdirectory()
    elif choice_type == "save":
        chosen = filedialog.asksaveasfilename(defaultextension=".sdlxliff")
    if chosen:
        path_variable.set(chosen)


def section(title):
    outer = ctk.CTkFrame(window, fg_color=CARD_DARK, border_color=BORDER_DARK, border_width=1, corner_radius=12)
    outer.pack(fill="x", padx=12, pady=(12, 4))
    ctk.CTkLabel(outer, text="  " + title, fg_color=GREEN_MAIN, text_color="black", font=("Segoe UI", 11, "bold"), anchor="w", height=36, corner_radius=12).pack(fill="x")
    body = ctk.CTkFrame(outer, fg_color=CARD_DARK, corner_radius=12)
    body.pack(fill="x", padx=10, pady=10)
    return body


def row(frame, row_number, label, path_variable, choice_type):
    ctk.CTkLabel(frame, text=label, text_color="white", font=("Segoe UI", 10)).grid(row=row_number, column=0, sticky="w", pady=4)
    ctk.CTkEntry(frame, textvariable=path_variable, fg_color=BG_DARK, text_color="white", border_color=BORDER_DARK, corner_radius=8, height=32).grid(row=row_number, column=1, sticky="ew", padx=8, pady=4)
    ctk.CTkButton(frame, text="Browse...", fg_color=GREEN_MAIN, hover_color=GREEN_DARK, text_color="black", font=("Segoe UI", 10, "bold"), corner_radius=8, width=90, height=32, command=lambda: choose_path(path_variable, choice_type)).grid(row=row_number, column=2, pady=4)
    frame.grid_columnconfigure(1, weight=1)


def button(frame, text, command):
    return ctk.CTkButton(frame, text=text, fg_color=GREEN_MAIN, hover_color=GREEN_DARK, text_color="black", font=("Segoe UI", 11, "bold"), corner_radius=10, height=38, command=command)


def run_job(keys, func, done_text, empty_text=""):
    # Jeden wspolny kod dla wszystkich 4 przyciskow, zamiast 4 razy tego samego try/except
    if any(not paths[key].get() for key in keys):
        messagebox.showwarning("Missing data", "Select all required paths.")
        return
    try:
        count = func(*[paths[key].get() for key in keys])
        if count == 0 and empty_text:
            message = empty_text
            messagebox.showwarning("Warning", message)
        else:
            message = done_text + str(count) + " segments."
            messagebox.showinfo("Done", message)
        status.set(message)
    except Exception as error:
        status.set("ERROR: " + str(error))
        messagebox.showerror("Error", str(error))


def on_export_click():
    run_job(["export_file", "export_folder"], converter.export_to_json, "Export done. Exported ")


def on_import_click():
    run_job(["import_file", "import_json", "import_save"], converter.import_to_sdlxliff, "Import done. Inserted ", "WARNING: Inserted 0. Check whether the output file is not the same file as the input one, or whether the JSON has target translations.")


def on_txt_export_click():
    run_job(["txt_json", "txt_folder"], converter.export_json_to_txt, "TXT done. Exported ")


def on_txt_import_click():
    run_job(["txt_to_import", "txt_json"], converter.import_txt_to_json, "TXT -> JSON done. Updated ", "WARNING: Updated 0. Check whether the number of lines in the TXT matches the number of segments in the JSON.")


# Sekcja 1
export_frame = section("Export SDLXLIFF -> JSON")
row(export_frame, 0, "SDLXLIFF file:", paths["export_file"], "file")
row(export_frame, 1, "Output folder:", paths["export_folder"], "folder")
button(export_frame, "Export to JSON", on_export_click).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))

# Sekcja 2
txt_frame = section("TXT: JSON <-> 2 TXT files")
row(txt_frame, 0, "export.json:", paths["txt_json"], "file")
row(txt_frame, 1, "Folder for TXT:", paths["txt_folder"], "folder")
row(txt_frame, 2, "TXT to import:", paths["txt_to_import"], "file")
button(txt_frame, "JSON -> 2 TXT files", on_txt_export_click).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0), padx=(0, 4))
button(txt_frame, "TXT -> JSON", on_txt_import_click).grid(row=3, column=2, sticky="ew", pady=(8, 0))

# Sekcja 3
import_frame = section("Import JSON -> SDLXLIFF")
row(import_frame, 0, "Original SDLXLIFF:", paths["import_file"], "file")
row(import_frame, 1, "Translated JSON:", paths["import_json"], "file")
row(import_frame, 2, "Save as:", paths["import_save"], "save")
button(import_frame, "Import to SDLXLIFF", on_import_click).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))

# Status
status_bar = ctk.CTkFrame(window, fg_color=GREEN_LIGHT, corner_radius=0, height=32)
status_bar.pack(fill="x", side="bottom")
ctk.CTkLabel(status_bar, textvariable=status, text_color="white", font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=5)

window.mainloop()