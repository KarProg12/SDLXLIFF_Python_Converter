#!/usr/bin/env python3
"""
Konwerter SDLXLIFF -> JSON + ekstrakcja source.

Użycie:
    python sdlxliff_to_json.py plik.sdlxliff
    python sdlxliff_to_json.py plik.zip

Dla archiwum ZIP program automatycznie wyszukuje w nim plik .sdlxliff.
Wyniki zapisuje obok pliku wejściowego:
    <nazwa>_converted.json  - wszystkie segmenty i ich metadane
    <nazwa>_source.txt      - tylko source spełniające kryteria
"""

from pathlib import Path
import argparse
import json
import zipfile
import xml.etree.ElementTree as ET


# W SDLXLIFF wartości conf mogą mieć m.in. takie postacie:
# Translated oraz ApprovedTranslation.
EXCLUDED_STATUSES = {
    "translated",
    "approvedtranslation",
    "translated approved",
    "translated/approved",
}


def local_name(tag):
    """Zwraca nazwę tagu bez przestrzeni nazw XML."""
    return tag.rsplit("}", 1)[-1]


def find_child(element, wanted_name):
    """Znajduje bezpośrednie dziecko po lokalnej nazwie tagu."""
    for child in element:
        if local_name(child.tag) == wanted_name:
            return child
    return None


def find_children(element, wanted_name):
    """Zwraca bezpośrednie dzieci o podanej lokalnej nazwie tagu."""
    return [
        child for child in element
        if local_name(child.tag) == wanted_name
    ]


def element_text(element):
    """Łączy tekst również z ewentualnych elementów inline XML."""
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def read_input(path):
    """Odczytuje SDLXLIFF bezpośrednio lub z archiwum ZIP."""
    path = Path(path)

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as archive:
            candidates = [
                name for name in archive.namelist()
                if name.lower().endswith((".sdlxliff", ".xliff"))
            ]

            if not candidates:
                raise ValueError("W archiwum ZIP nie znaleziono pliku SDLXLIFF/XLIFF.")

            if len(candidates) > 1:
                print("Znaleziono kilka plików XLIFF. Używam pierwszego:")
                for name in candidates:
                    print(f"  - {name}")

            selected_name = candidates[0]
            return archive.read(selected_name), Path(selected_name).stem

    return path.read_bytes(), path.stem


def marker_text_map(container):
    """
    Buduje mapę mid -> tekst segmentu z elementów <mrk mtype="seg">.
    """
    result = {}

    if container is None:
        return result

    for marker in container.iter():
        if local_name(marker.tag) != "mrk":
            continue
        if marker.get("mtype") != "seg":
            continue

        marker_id = marker.get("mid")
        if marker_id is not None:
            result[marker_id] = element_text(marker)

    return result


def is_100_percent(value):
    """Sprawdza, czy procent dopasowania wynosi dokładnie 100."""
    if value is None:
        return False

    normalized = value.strip().replace("%", "").replace(",", ".")
    try:
        return float(normalized) == 100.0
    except ValueError:
        return False


def is_excluded(status, match):
    """Zwraca True, jeśli segment należy pominąć."""
    normalized_status = (status or "").strip().casefold()

    return (
        normalized_status in EXCLUDED_STATUSES
        or is_100_percent(match)
    )


def parse_sdlxliff(xml_bytes):
    """Konwertuje segmenty SDLXLIFF do listy słowników Pythona."""
    root = ET.fromstring(xml_bytes)
    segments = []

    for unit in root.iter():
        if local_name(unit.tag) != "trans-unit":
            continue

        source_element = find_child(unit, "source")
        seg_source_element = find_child(unit, "seg-source")
        target_element = find_child(unit, "target")
        seg_defs_element = find_child(unit, "seg-defs")

        # W SDLXLIFF tekst segmentu źródłowego jest zwykle w:
        # seg-source -> mrk (mtype="seg", mid="...")
        source_by_id = marker_text_map(seg_source_element)
        target_by_id = marker_text_map(target_element)

        # Metadane segmentów SDL są przechowywane w seg-defs -> seg.
        definitions = (
            find_children(seg_defs_element, "seg")
            if seg_defs_element is not None else []
        )

        if definitions:
            for definition in definitions:
                segment_id = definition.get("id")
                source_text = source_by_id.get(segment_id)

                # Fallback dla prostych plików, w których nie ma markerów.
                if source_text is None and len(definitions) == 1:
                    source_text = element_text(source_element)

                target_text = target_by_id.get(segment_id)
                if target_text is None and len(definitions) == 1:
                    target_text = element_text(target_element)

                status = definition.get("conf")
                match = definition.get("percent")

                segments.append({
                    "trans_unit_id": unit.get("id"),
                    "segment_id": segment_id,
                    "source": source_text or "",
                    "target": target_text or "",
                    "status": status,
                    "match_percent": match,
                    "excluded": is_excluded(status, match),
                })
        else:
            # Awaryjna obsługa zwykłego XLIFF bez SDL seg-defs.
            segments.append({
                "trans_unit_id": unit.get("id"),
                "segment_id": None,
                "source": element_text(source_element),
                "target": element_text(target_element),
                "status": target_element.get("state") if target_element is not None else None,
                "match_percent": None,
                "excluded": is_excluded(
                    target_element.get("state") if target_element is not None else None,
                    None,
                ),
            })

    return segments


def main():
    parser = argparse.ArgumentParser(
        description="Konwertuje SDLXLIFF/XLIFF do JSON i wyodrębnia source."
    )
    parser.add_argument("input_file", help="Ścieżka do pliku .sdlxliff lub .zip")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    xml_bytes, base_name = read_input(input_path)
    segments = parse_sdlxliff(xml_bytes)

    selected = [
        segment for segment in segments
        if not segment["excluded"] and segment["source"]
    ]

    output_data = {
        "input_file": input_path.name,
        "total_segments": len(segments),
        "selected_segments_count": len(selected),
        "excluded_statuses": sorted(EXCLUDED_STATUSES),
        "excluded_rule": "status Translated/Translated Approved lub match 100%",
        "segments": segments,
        "selected_segments": selected,
    }

    json_path = input_path.parent / f"{base_name}_converted.json"
    txt_path = input_path.parent / f"{base_name}_source.txt"

    json_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    txt_path.write_text(
        "\n".join(segment["source"] for segment in selected),
        encoding="utf-8",
    )

    print(f"Przeanalizowano segmentów: {len(segments)}")
    print(f"Segmentów do wyodrębnienia: {len(selected)}")
    print(f"JSON: {json_path}")
    print(f"TXT:  {txt_path}")


if __name__ == "__main__":
    main()
