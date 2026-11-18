import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Importujemy funkcje z drugiego pliku
from converter import eksportuj_do_json, importuj_do_sdlxliff, eksportuj_json_do_txt, importuj_txt_do_json


# --- 1. Okno glowne ---
okno = tk.Tk()
okno.title("TransmAIte (SDLXLIFF <- 2x TXT -> JSON)")
okno.geometry("640x545")

# --- 2. Pudeleczka na sciezki ---
# Kazde pudeleczko przechowuje jedna sciezke wybrana przez uzytkownika.
sciezki = {}
for nazwa in ["eksport_plik", "eksport_folder",
              "import_plik", "import_json", "import_zapisz",
              "txt_json", "txt_folder", "txt_do_importu"]:
    sciezki[nazwa] = tk.StringVar()


def wybierz_sciezke(pudeleczko, jaki_typ):
    """Otwiera okienko wyboru pliku/folderu i zapisuje wybor do pudeleczka."""
    wybrana = ""
    if jaki_typ == "plik":
        wybrana = filedialog.askopenfilename()
    elif jaki_typ == "folder":
        wybrana = filedialog.askdirectory()
    elif jaki_typ == "zapisz":
        wybrana = filedialog.asksaveasfilename(defaultextension=".sdlxliff")

    if wybrana:
        pudeleczko.set(wybrana)


def dodaj_rzad(pudelko, numer_rzedu, napis, pudeleczko, jaki_typ):
    """Jeden rzad w okienku: napis + pole na sciezke + przycisk Browse."""
    ttk.Label(pudelko, text=napis).grid(row=numer_rzedu, column=0, sticky="w", pady=2)
    ttk.Entry(pudelko, textvariable=pudeleczko).grid(row=numer_rzedu, column=1, sticky="ew", padx=6, pady=2)
    ttk.Button(pudelko, text="Browse...", command=lambda: wybierz_sciezke(pudeleczko, jaki_typ)).grid(row=numer_rzedu, column=2, pady=2)
    pudelko.columnconfigure(1, weight=1)


def pokaz_blad_lub_wykonaj(co_robimy):
    """Wspolna obsluga bledow: jesli cos sie wywali, pokaz okienko z bledem."""
    try:
        wiadomosc = co_robimy()
        status.set(wiadomosc)
        if wiadomosc.startswith("UWAGA"):
            messagebox.showwarning("Uwaga", wiadomosc)
        else:
            messagebox.showinfo("Gotowe", wiadomosc)

    except Exception as error:
        status.set("BŁĄD: " + str(error))
        messagebox.showerror("Błąd", str(error))


# --- 3. Co robi kazdy przycisk ---

def kliknij_eksport():
    if not sciezki["eksport_plik"].get() or not sciezki["eksport_folder"].get():
        messagebox.showwarning("Brakuje danych", "Wybierz plik SDLXLIFF i folder wyjsciowy.")
        return

    def zadanie():
        liczba = eksportuj_do_json(sciezki["eksport_plik"].get(), sciezki["eksport_folder"].get())
        return "Eksport gotowy. Wyeksportowano " + str(liczba) + " segmentow."

    pokaz_blad_lub_wykonaj(zadanie)


def kliknij_import():
    if not sciezki["import_plik"].get() or not sciezki["import_json"].get() or not sciezki["import_zapisz"].get():
        messagebox.showwarning("Brakuje danych", "Wybierz wszystkie 3 sciezki do importu.")
        return

    def zadanie():
        liczba = importuj_do_sdlxliff(sciezki["import_plik"].get(), sciezki["import_json"].get(), sciezki["import_zapisz"].get())
        if liczba == 0:
            return "UWAGA: Wstawiono 0. Sprawdź, czy plik wyjściowy to nie ten sam plik co wejściowy, albo czy JSON ma tłumaczenia target."
        return "Import gotowy. Wstawiono " + str(liczba) + " segmentow."

    pokaz_blad_lub_wykonaj(zadanie)


def kliknij_txt_eksport():
    if not sciezki["txt_json"].get() or not sciezki["txt_folder"].get():
        messagebox.showwarning("Brakuje danych", "Wybierz export.json i folder wyjsciowy.")
        return

    def zadanie():
        liczba = eksportuj_json_do_txt(sciezki["txt_json"].get(), sciezki["txt_folder"].get())
        return "TXT gotowe. Wyeksportowano " + str(liczba) + " segmentow."

    pokaz_blad_lub_wykonaj(zadanie)


def kliknij_txt_import():
    if not sciezki["txt_do_importu"].get() or not sciezki["txt_json"].get():
        messagebox.showwarning("Brakuje danych", "Wybierz plik TXT i export.json do aktualizacji.")
        return

    def zadanie():
        liczba = importuj_txt_do_json(sciezki["txt_do_importu"].get(), sciezki["txt_json"].get())
        if liczba == 0:
            return "UWAGA: Zaktualizowano 0. Sprawdz, czy liczba linii w TXT pasuje do liczby segmentow w JSON."
        return "TXT -> JSON gotowe. Zaktualizowano " + str(liczba) + " segmentow."

    pokaz_blad_lub_wykonaj(zadanie)


# --- 4. Budujemy okienko: 3 pudelka ---

pudelko_eksport = ttk.LabelFrame(okno, text=" Eksport SDLXLIFF -> JSON ", padding=8)
pudelko_eksport.pack(fill="x", padx=10, pady=(10, 5))
dodaj_rzad(pudelko_eksport, 0, "Plik SDLXLIFF:", sciezki["eksport_plik"], "plik")
dodaj_rzad(pudelko_eksport, 1, "Folder wyjsciowy:", sciezki["eksport_folder"], "folder")
ttk.Button(pudelko_eksport, text="Eksportuj do JSON", command=kliknij_eksport).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))

pudelko_txt = ttk.LabelFrame(okno, text=" TXT: JSON <-> 2 pliki TXT ", padding=8)
pudelko_txt.pack(fill="x", padx=10, pady=5)
dodaj_rzad(pudelko_txt, 0, "export.json:", sciezki["txt_json"], "plik")
dodaj_rzad(pudelko_txt, 1, "Folder na TXT:", sciezki["txt_folder"], "folder")
dodaj_rzad(pudelko_txt, 2, "TXT do importu:", sciezki["txt_do_importu"], "plik")
ttk.Button(pudelko_txt, text="JSON -> 2 pliki TXT", command=kliknij_txt_eksport).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
ttk.Button(pudelko_txt, text="TXT -> JSON", command=kliknij_txt_import).grid(row=3, column=2, sticky="ew", pady=(6, 0))

pudelko_import = ttk.LabelFrame(okno, text=" Import JSON -> SDLXLIFF ", padding=8)
pudelko_import.pack(fill="x", padx=10, pady=5)
dodaj_rzad(pudelko_import, 0, "Oryginalny SDLXLIFF:", sciezki["import_plik"], "plik")
dodaj_rzad(pudelko_import, 1, "Przetlumaczony JSON:", sciezki["import_json"], "plik")
dodaj_rzad(pudelko_import, 2, "Zapisz jako:", sciezki["import_zapisz"], "zapisz")
ttk.Button(pudelko_import, text="Importuj do SDLXLIFF", command=kliknij_import).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))

# --- 5. Linia statusu na dole + start ---
status = tk.StringVar(value="Gotowy.")
ttk.Label(okno, textvariable=status).pack(anchor="w", padx=12, pady=8)

okno.mainloop()
