# SDLXLIFF -> JSON

## Zawartość
- `sdlxliff_to_json.py` — program konwertujący SDLXLIFF (lub ZIP z SDLXLIFF) do JSON i wyodrębniający angielskie source.
- `CPQ_translations_Tool_holder_2026-10-14_converted.json` — wynik konwersji przesłanego przykładowego pliku.
- `CPQ_translations_Tool_holder_2026-10-14_source.txt` — source spełniające kryteria (w tym przykładzie plik jest pusty, bo nie znaleziono pasujących segmentów).
- `CPQ_translations_Tool_holder_2026-10-14.xlsx.zip` — oryginalne archiwum wejściowe.

## Uruchomienie
Wymagany Python 3.9+; nie trzeba instalować dodatkowych bibliotek.

```bash
python sdlxliff_to_json.py CPQ_translations_Tool_holder_2026-10-14.xlsx.zip
```

Można też podać bezpośrednio plik `.sdlxliff`:

```bash
python sdlxliff_to_json.py plik.sdlxliff
```

Program tworzy obok pliku wejściowego:
- `<nazwa>_converted.json` — wszystkie segmenty wraz ze statusem i procentem match.
- `<nazwa>_source.txt` — wyłącznie teksty `source`, które nie są oznaczone jako `Translated`, `Translated Approved` / `ApprovedTranslation` ani 100% match.

Uwaga: w tym konkretnym pliku SDLXLIFF znaleziono 100 segmentów. Wszystkie mają status `Translated` lub `ApprovedTranslation`, więc wynik filtrowania zawiera 0 segmentów.
