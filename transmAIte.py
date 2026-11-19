# Uproszczone GUI - ttk
# Nic nie trzeba instalowac - ttk jest w Pythonie

from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

from converter import Converter as CNV

class TransMAiTE:
    def __init__(self):
        # Kolory z ikony aplikacji: ciemne tlo + zielen z ikony
        self.BG_DARK = "#232323"
        self.CARD_DARK = "#2E2E2E"
        self.BORDER_DARK = "#3A3A3A"
        self.GREEN_DARK = "#18863F"
        self.GREEN_MAIN = "#5ABC6F"
        self.GREEN_LIGHT = "#2A3D30"

        self.root_win = tk.Tk()
        self.root_win.title("TransMAiTE")
        self.root_win.geometry("685x778")
        self.root_win.configure(bg=self.BG_DARK)

        # Style ttk - kolory ustawiamy RAZ tutaj, widgety tylko wybieraja styl
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Top.TFrame", background=self.GREEN_DARK)
        self.style.configure("Top.TLabel", background=self.GREEN_DARK, foreground="white", font=("Segoe UI", 14, "bold"))
        self.style.configure("TopSmall.TLabel", background=self.GREEN_DARK, foreground="#D6F5DD", font=("Segoe UI", 9))
        self.style.configure("Card.TFrame", background=self.CARD_DARK, bordercolor=self.BORDER_DARK, borderwidth=1, relief="solid")
        self.style.configure("Body.TFrame", background=self.CARD_DARK)
        self.style.configure("Title.TLabel", background=self.GREEN_MAIN, foreground="black", font=("Segoe UI", 10, "bold"))
        self.style.configure("Row.TLabel", background=self.CARD_DARK, foreground="white", font=("Segoe UI", 9))
        self.style.configure("TEntry", fieldbackground=self.BG_DARK, foreground="white", insertcolor="white", font=("Segoe UI", 9), padding=3)
        self.style.configure("Green.TButton", background=self.GREEN_MAIN, foreground="black", font=("Segoe UI", 9, "bold"), padding=3)
        self.style.map("Green.TButton", background=[("active", self.GREEN_DARK), ("pressed", self.GREEN_DARK)])
        self.style.configure("BigGreen.TButton", background=self.GREEN_MAIN, foreground="black", font=("Segoe UI", 10, "bold"), padding=4)
        self.style.map("BigGreen.TButton", background=[("active", self.GREEN_DARK), ("pressed", self.GREEN_DARK)])
        self.style.configure("Status.TFrame", background=self.GREEN_LIGHT)
        self.style.configure("Status.TLabel", background=self.GREEN_LIGHT, foreground="white", font=("Segoe UI", 9))

        # Gorny pasek
        top = ttk.Frame(self.root_win, style="Top.TFrame", height=40)
        top.pack(fill="x")
        top.pack_propagate(False)
        ttk.Label(top, text="  TransMAiTE", style="Top.TLabel").pack(side="left")
        ttk.Label(top, text="SDLXLIFF  <->  TXT  <->  JSON  ", style="TopSmall.TLabel").pack(side="right", padx=12)

        # Sciezki - jedna petla, tak jak bylo wczesniej, bo to tu jest czytelniejsze
        self.paths = {}
        for path_key in ["export_file", "export_folder",
                         "import_file", "import_json", "import_save",
                         "txt_json", "txt_folder", "txt_to_import"]:
            self.paths[path_key] = tk.StringVar()

        self.status = tk.StringVar(value="Ready.")

        self.build_ui()
        self.converter = CNV()

    def choose_path(self, path_variable, choice_type):
        chosen = ""
        if choice_type == "file":
            chosen = filedialog.askopenfilename()
        elif choice_type == "folder":
            chosen = filedialog.askdirectory()
        elif choice_type == "save":
            chosen = filedialog.asksaveasfilename(defaultextension=".sdlxliff")
        if chosen:
            path_variable.set(chosen)

    def section(self, title):
        outer = ttk.Frame(self.root_win, style="Card.TFrame")
        outer.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(outer, text="  " + title, style="Title.TLabel", anchor="w").pack(fill="x", ipady=8)
        body = ttk.Frame(outer, style="Body.TFrame")
        body.pack(fill="x", padx=10, pady=10)
        return body

    def row(self, frame, row_number, label, path_variable, choice_type):
        ttk.Label(frame, text=label, style="Row.TLabel").grid(row=row_number, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=path_variable).grid(row=row_number, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame, text="Browse...", style="Green.TButton", command=lambda: self.choose_path(path_variable, choice_type)).grid(row=row_number, column=2, pady=4)
        frame.grid_columnconfigure(1, weight=1)

    def button(self, frame, text, command):
        return ttk.Button(frame, text=text, style="BigGreen.TButton", command=command)

    def run_task(self, keys, func, done_text, empty_text=""):
        # Jeden wspolny kod dla wszystkich 4 przyciskow, zamiast 4 razy tego samego try/except
        if any(not self.paths[key].get() for key in keys):
            messagebox.showwarning("Missing data", "Select all required paths.")
            return
        try:
            count = func(*[self.paths[key].get() for key in keys])
            if count == 0 and empty_text:
                message = empty_text
                messagebox.showwarning("Warning", message)
            else:
                message = done_text + str(count) + " segments."
                messagebox.showinfo("Done", message)
            self.status.set(message)
        except Exception as error:
            self.status.set("ERROR: " + str(error))
            messagebox.showerror("Error", str(error))

    def on_export_click(self):
        self.run_task(["export_file", "export_folder"], self.converter.export_to_json, "Export done. Exported ")

    def on_import_click(self):
        self.run_task(["import_file", "import_json", "import_save"], self.converter.import_to_sdlxliff, "Import done. Inserted ", "WARNING: Inserted 0. Check whether the output file is not the same file as the input one, or whether the JSON has target translations.")

    def on_txt_export_click(self):
        self.run_task(["txt_json", "txt_folder"], self.converter.export_json_to_txt, "TXT done. Exported ")

    def on_txt_import_click(self):
        self.run_task(["txt_to_import", "txt_json"], self.converter.import_txt_to_json, "TXT -> JSON done. Updated ", "WARNING: Updated 0. Check whether the number of lines in the TXT matches the number of segments in the JSON.")

    def build_ui(self):
        # Sekcja 1
        export_frame = self.section("Export SDLXLIFF ==> JSON - exports only segments without statuses:\n"
                                    "    Translated, ApprovedTranslation, ApprovedSignOff, locked='true'")
        self.row(export_frame, 0, "SDLXLIFF file:", self.paths["export_file"], "file")
        self.row(export_frame, 1, "Output folder:", self.paths["export_folder"], "folder")
        self.button(export_frame, "Export SDLXLIFF to JSON", self.on_export_click).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        # Sekcja 2
        txt_frame = self.section("JSON <==> 2x TXT files\n  ! ! NUMBER OF LINES IN source.txt AND target.txt MUST BE THE SAME TO IMPORT target.txt to JSON ! !\n"
                                 "  - source.txt (all sources except filtered ones in section above),\n  - target.txt (empty file for translated sources)")
        self.row(txt_frame, 0, "export.json:", self.paths["txt_json"], "file")
        self.row(txt_frame, 1, "Folder for TXT:", self.paths["txt_folder"], "folder")
        self.row(txt_frame, 2, "TXT to import:", self.paths["txt_to_import"], "file")
        self.button(txt_frame, "Extract JSON to source.txt and target.txt files", self.on_txt_export_click).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0), padx=(0, 4))
        self.button(txt_frame, "translated target.txt\nback to JSON targets", self.on_txt_import_click).grid(row=3, column=2, sticky="ew", pady=(8, 0))

        # Sekcja 3
        import_frame = self.section("Import JSON ==> SDLXLIFF - imports targets from translated JSON to SDLXLIFF's targets")
        self.row(import_frame, 0, "Original SDLXLIFF:", self.paths["import_file"], "file")
        self.row(import_frame, 1, "Translated JSON:", self.paths["import_json"], "file")
        self.row(import_frame, 2, "Save as:", self.paths["import_save"], "save")
        self.button(import_frame, "Import to SDLXLIFF", self.on_import_click).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        # Status
        status_bar = ttk.Frame(self.root_win, style="Status.TFrame", height=32)
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status, style="Status.TLabel").pack(anchor="w", padx=14, pady=5)

    def run(self):
        self.root_win.mainloop()

if __name__ == "__main__":
    plugin = TransMAiTE()
    plugin.run()