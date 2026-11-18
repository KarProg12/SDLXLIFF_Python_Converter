# TransmAIte — SDLXLIFF ↔ JSON / TXT Converter

Aplikacja desktopowa napisana w Pythonie, która ułatwia tłumaczenie plików **SDLXLIFF** (stosowanych m.in. w programie Trados Studio) za pomocą modeli AI (LLM) lub zewnętrznych narzędzi tekstowych. Program wyciąga nieprzetłumaczone segmenty wraz z tagami XML, konwertuje je do wygodnych formatów pośrednich (**JSON** oraz par plików **TXT**), a następnie bezpiecznie wstrzykuje gotowe tłumaczenia z powrotem do struktury pliku `.sdlxliff`.

## ✨ Główne funkcjonalności

* **Inteligentny eksport SDLXLIFF → JSON (`eksportuj_do_json`):**
  * Filtruje segmenty — eksportuje tylko te nieprzetłumaczone i niezablokowane (pomija statusy `Translated`, `ApprovedTranslation`, `ApprovedSignOff` oraz segmenty z atrybutem `locked="true"`).
  * Zachowuje identyfikatory (`trans-unit_id`, `seg_id`), istniejące robocze tłumaczenia oraz wewnętrzne tagi formatujące XML (np. `<g>`, `<x/>`).
  * Przetwarza plik strumieniowo (`ET.iterparse`), co ogranicza zużycie pamięci przy dużych plikach.
* **Dwukierunkowa konwersja JSON ↔ 2x TXT (`eksportuj_json_do_txt`, `importuj_txt_do_json`):**
  * Generuje dwa zsynchronizowane liniami pliki: `export_source.txt` (tylko do odczytu) oraz `export_target.txt` (do tłumaczenia).
  * Zamienia wewnętrzne znaki nowej linii na sekwencję `\n`, gwarantując układ **1 linia = 1 segment**.
  * Przy imporcie sprawdza zgodność liczby linii między plikiem TXT a segmentami w JSON oraz raportuje statystyki (zmienione, bez zmian, puste).
* **Bezpieczny import JSON → SDLXLIFF (`importuj_do_sdlxliff`):**
  * Tworzy automatyczną kopię zapasową pliku źródłowego z rozszerzeniem `.bak`.
  * Blokuje przypadkowe nadpisanie oryginalnego pliku wejściowego.
  * Weryfikuje liczbę tagów (`<`) między źródłem a tłumaczeniem i ostrzega w konsoli w przypadku rozbieżności.
  * Odtwarza wymagane przez Tradosa przestrzenie nazw XML (`xliff` / `sdl`) oraz ustawia status zaimportowanych segmentów na `Draft`.
* **Prosty interfejs graficzny (GUI):**
  * Intuicyjne okno podzielone na trzy sekcje robocze z oknami wyboru plików/folderów oraz paskiem statusu na dole ekranu.

## 🛠️ Technologie

Projekt opiera się w 100% na **bibliotece standardowej Pythona 3** — nie wymaga instalowania żadnych zewnętrznych pakietów (`pip`):

* `tkinter` (`filedialog`, `messagebox`, `ttk`) — interfejs graficzny aplikacji
* `xml.etree.ElementTree` — parsowanie, rekonstrukcja tagów i zapis plików SDLXLIFF
* `json` — obsługa pośredniego formatu danych `export.json`
* `os`, `shutil` — zarządzanie ścieżkami, tworzenie katalogów i kopii zapasowych `.bak`

## 📂 Struktura repozytorium

* `transmAIte.py` — główny plik uruchomieniowy zawierający interfejs graficzny (`tkinter`) oraz obsługę zdarzeń i komunikatów błędów.
* `converter.py` — warstwa logiki biznesowej odpowiedzialna za parsowanie XML, obsługę przestrzeni nazw oraz konwersję między formatami `.sdlxliff`, `.json` i `.txt`.

## 🚀 Instalacja i uruchomienie

1. **Upewnij się, że masz zainstalowanego Pythona 3** (wraz z modułem `tkinter`, który jest domyślnie dołączany w instalatorach dla Windows i macOS).
2. **Sklonuj repozytorium:**
   ```bash
   git clone https://github.com
   cd SDLXLIFF_Python_Converter
   ```
3. **Uruchom program:**
   ```bash
   python transmAIte.py
   ```

## 📖 Instrukcja krok po kroku (Workflow)

1. **Eksport segmentów z SDLXLIFF:**
   * W sekcji **Eksport SDLXLIFF -> JSON** wybierz plik `.sdlxliff` oraz folder wyjściowy.
   * Kliknij **Eksportuj do JSON**, aby utworzyć plik `export.json`.
2. **Tłumaczenie (wybierz jedną z dróg):**
   * **Ścieżka TXT (wygodna dla AI / edytorów):** W sekcji **TXT: JSON <-> 2 pliki TXT** wskaż plik `export.json` i folder docelowy, a następnie kliknij **JSON -> 2 pliki TXT**. Przetłumacz zawartość pliku `export_target.txt` (zachowując dokładnie tę samą liczbę linii oraz tagi XML, np. `<g id="1">...</g>`), po czym wczytaj go z powrotem przyciskiem **TXT -> JSON**.
   * **Ścieżka JSON:** Uzupełnij bezpośrednio wartości klucza `"target"` w pliku `export.json`.
3. **Zapis gotowego pliku SDLXLIFF:**
   * W sekcji **Import JSON -> SDLXLIFF** wybierz oryginalny plik `.sdlxliff`, zaktualizowany `export.json` oraz nową nazwę/ścieżkę pliku wynikowego.
   * Kliknij **Importuj do SDLXLIFF**. Wynikowy plik jest gotowy do otwarcia i weryfikacji w programie CAT (np. Trados Studio).

## ⚠️ Ważne wskazówki

* **Nie usuwaj ani nie zmieniaj liczby linii** w pliku `*_target.txt` — program dopasowuje tłumaczenia do segmentów na podstawie numeru linii.
* **Zachowuj tagi XML** widoczne w segmencie źródłowym (np. `<g id="1">tekst</g>`), aby uniknąć błędów struktury w programie Trados Studio.
* Plik wyjściowy `.sdlxliff` musi mieć inną nazwę lub lokalizację niż plik wejściowy.
