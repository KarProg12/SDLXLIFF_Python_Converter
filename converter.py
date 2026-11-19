# Co robi ten plik?
# 1. Czyta plik .sdlxliff i zapisuje segmenty do export.json
# 2. Czyta export.json i wstawia tlumaczenia z powrotem do .sdlxliff
# 3. Zamienia JSON na 2 pliki TXT i z powrotem
# Uzywamy tylko: funkcje, listy, slowniki, for, if, open(), json, try/except

import json
import os
import shutil
import xml.etree.ElementTree as ET

class Converter:
    def __init__(self):
        # To sa "nazwiska" tagow w pliku XML. Python potrzebuje ich, zeby znalezc tagi.
        # Nie musisz ich rozumiec na pamiec - po prostu kopiuj je tak jak sa.
        self.NAMESPACES = {"sdl": "http://sdl.com/FileTypes/SdlXliff/1.0", "xliff": "urn:oasis:names:tc:xliff:document:1.2"}
        self.XLIFF = "{urn:oasis:names:tc:xliff:document:1.2}"
        self.SDL = "{http://sdl.com/FileTypes/SdlXliff/1.0}"
        self.XML_NS = "{http://www.w3.org/XML/1998/namespace}"

        # Te statusy znacza: "juz przetlumaczone, nie ruszaj"
        self.TRANSLATED_STATUSES = ["Translated", "ApprovedTranslation", "ApprovedSignOff"]

        self.changed_by_user = 0
        self.unchanged_segments = 0
        self.empty_segments = 0

    def read_json(self, json_file):
        with open(json_file, encoding="utf-8") as file:
            return json.load(file)

    def write_json(self, json_file, data):
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def find_markers(self, parent):
        # {mid: <mrk>} tylko dla znacznikow segmentow, None -> pusty slownik
        if parent is None:
            return {}
        return {str(m.get("mid")): m for m in parent.findall(".//xliff:mrk", self.NAMESPACES) if m.get("mtype") == "seg" and m.get("mid") is not None}

    def clean(self, name):
        # "{...}g" -> "g", "{sdl...}g" -> "sdl:g", "{xml...}lang" -> "xml:lang"
        if name.startswith(self.XML_NS):
            return "xml:" + name.split("}", 1)[-1]
        if name.startswith(self.SDL):
            return "sdl:" + name.split("}", 1)[-1]
        if name.startswith("{"):
            return name.split("}", 1)[-1]
        return name

    def text_from_element(self, element):
        """Takes the text from an XML element together with the tags inside it, e.g. <g>.
        Example: Hello <g>world</g> -> "Hello <g>world</g>"
        """
        if element is None:
            return ""
        pieces = []  # Zbieramy kawalki tekstu, na koncu je laczymy.
        if element.text:  # Tekst przed pierwszym tagiem w srodku
            pieces.append(element.text)
        for child in element:
            # Atrybuty tagu, np. id="1" - & i " musza byc zapisane inaczej, inaczej plik sie zepsuje
            attributes = "".join(" " + self.clean(n) + '="' + v.replace("&", "&amp;").replace('"', "&quot;") + '"' for n, v in child.attrib.items())
            inner_text = self.text_from_element(child)  # Tekst w srodku tagu (funkcja wywoluje sama siebie - rekurencja)
            name = self.clean(child.tag)
            if inner_text:
                pieces.append("<" + name + attributes + ">" + inner_text + "</" + name + ">")
            else:
                pieces.append("<" + name + attributes + "/>")
            if child.tail:  # Tekst PO tym tagu
                pieces.append(child.tail)
        return "".join(pieces)

    def add_namespace(self, element):
        """AI sometimes returns a plain <g>, but Trados wants a <g> with a namespace.
        This function adds it to every plain tag.
        """
        for child in element:
            if not child.tag.startswith("{"):
                child.tag = self.XLIFF + child.tag
            self.add_namespace(child)

    def export_to_json_and_txts(self, sdlxliff_file, output_folder):
        """Reads .sdlxliff and saves export.json in the given folder."""
        segments = []
        # Czytami plik XML po jednym trans-unit
        for _, trans_unit in ET.iterparse(sdlxliff_file, events=('end',)):
            if not trans_unit.tag.endswith("}trans-unit"):
                continue
            source_element = trans_unit.find("xliff:seg-source", self.NAMESPACES)
            seg_defs = trans_unit.find("sdl:seg-defs", self.NAMESPACES)
            if source_element is None or seg_defs is None:
                trans_unit.clear()
                continue
            statuses = {str(s.get("id")): [s.get("conf"), s.get("locked")] for s in seg_defs.findall("sdl:seg", self.NAMESPACES) if s.get("id") is not None}
            old_translations = {mid: self.text_from_element(m) for mid, m in self.find_markers(trans_unit.find("xliff:target", self.NAMESPACES)).items()}
            for seg_id, marker in self.find_markers(source_element).items():
                if seg_id not in statuses:
                    continue
                status, locked = statuses[seg_id]
                if locked == "true" or status in self.TRANSLATED_STATUSES:
                    continue
                segments.append({"trans-unit_id": str(trans_unit.get("id")), "seg_id": seg_id, "status": status or "Not Translated",
                                 "source": self.text_from_element(marker), "target": old_translations.get(seg_id, "")})
            trans_unit.clear()
        # Zapisujemy do pliku JSON
        os.makedirs(output_folder, exist_ok=True)
        self.write_json(os.path.join(output_folder, "export.json"), {"segments": segments})
        print("Done! Exported", len(segments), "segments.")

        # Otwiera 2 pliki source i target .txt, w source.txt są wszystkie wyciągnięte segmenty
        # a target.txt jest pusty bo czeka na wklejenie przetłumaczonego tekstu
        with open(os.path.join(output_folder, "source.txt"), "w", encoding="utf-8") as source_file:
            with open(os.path.join(output_folder, "target.txt"), "w", encoding="utf-8") as target_file:
                for segment in segments:
                    source_file.write(segment["source"].replace("\n", "\\n") + "\n")
        print("TXT done.")
        return len(segments)

    def import_to_sdlxliff(self, sdlxliff_file, json_file, output_file):
        """Inserts translations from JSON back into the .sdlxliff file."""
        if output_file == sdlxliff_file:
            print("NOT SAVED: the output file is the same file as the input file!")
            return 0
        backup_folder = os.path.dirname(json_file)
        backup_file = os.path.join(backup_folder, os.path.basename(sdlxliff_file) + ".bak")
        if not os.path.exists(backup_file):
            shutil.copy(sdlxliff_file, backup_file)
        data = self.read_json(json_file)
        # Slownik: (id_jednostki, id_segmentu) -> tlumaczenie
        translations = {(str(s["trans-unit_id"]), str(s["seg_id"])): s.get("target", "").strip() for s in data["segments"] if s.get("target", "").strip()}
        tree = ET.parse(sdlxliff_file)
        root = tree.getroot()
        inserted = 0
        skipped = 0
        changed_by_user = 0
        for trans_unit in root.findall(".//xliff:trans-unit", self.NAMESPACES):
            trans_unit_id = str(trans_unit.get("id"))
            target_element = trans_unit.find("xliff:target", self.NAMESPACES)
            seg_defs = trans_unit.find("sdl:seg-defs", self.NAMESPACES)
            if target_element is None or seg_defs is None:
                skipped += 1
                continue
            markers = self.find_markers(target_element)  # Znajdz istniejace znaczniki <mrk> w celu: id -> element
            sources = {mid: self.text_from_element(m) for mid, m in self.find_markers(trans_unit.find("xliff:seg-source", self.NAMESPACES)).items()}
            for seg_def in seg_defs.findall("sdl:seg", self.NAMESPACES):
                seg_id = seg_def.get("id")
                if seg_id is None:  # seg bez id - nie da sie go dopasowac do tlumaczenia
                    continue
                if (trans_unit_id, seg_id) not in translations:
                    continue
                if seg_id not in markers:  # Jesli nie ma znacznika w celu, tworzymy nowy
                    markers[seg_id] = ET.SubElement(target_element, self.XLIFF + "mrk")
                    markers[seg_id].set("mtype", "seg")
                    markers[seg_id].set("mid", seg_id)
                marker = markers[seg_id]
                new_text = translations[(trans_unit_id, seg_id)]
                old_text = self.text_from_element(marker)
                if old_text != new_text:
                    changed_by_user += 1
                source_text = sources.get(seg_id, "")
                if source_text.count("<") != new_text.count("<"):
                    print(f"WARNING: different number of tags in segment {seg_id}")
                    print(f"Source: {source_text}")
                    print(f"Translation: {new_text}")
                # Czyscimy stary tekst, ale zachowujemy atrybuty
                old_attributes, old_tail = dict(marker.attrib), marker.tail
                marker.clear()
                for name, value in old_attributes.items():
                    marker.set(name, value)
                marker.set("mtype", "seg")
                marker.set("mid", seg_id)
                marker.tail = old_tail
                # Probujemy wstawic tekst z tagami jako XML. Jesli sie nie uda (np. zwykly znak &), wstawiamy jako zwykly tekst.
                try:
                    fragment = ET.fromstring('<wrap xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:sdl="http://sdl.com/FileTypes/SdlXliff/1.0">' + new_text + "</wrap>")
                    self.add_namespace(fragment)
                    marker.text = fragment.text
                    for child in fragment:
                        marker.append(child)
                except ET.ParseError:
                    marker.text = new_text
                seg_def.set("conf", "Draft")
                inserted += 1
        # Rejestrujemy przestrzenie nazw, zeby plik wygladal ladnie
        ET.register_namespace("sdl", "http://sdl.com/FileTypes/SdlXliff/1.0")
        ET.register_namespace("", "urn:oasis:names:tc:xliff:document:1.2")
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"{inserted=}")
        print(f"{skipped=}")
        print(f"Segments changed by user: {changed_by_user}")
        return inserted

    def import_txt_to_json(self, txt_file, json_file):
        """Reads the translated TXT and inserts the translations back into the JSON."""
        data = self.read_json(json_file)
        with open(txt_file, encoding="utf-8") as file:
            lines = [line.rstrip("\n").replace("\\n", "\n") for line in file]
        while len(lines) > len(data["segments"]) and lines[-1] == "":
            lines.pop()
        if len(lines) != len(data["segments"]):
            print("ERROR: the number of lines in the TXT does not match the number of segments!\n"
                  f"TXT lines: {len(lines)}\n"
                  f"JSON segments: {len(data['segments'])}")
            return 0
        self.changed_by_user = self.unchanged_segments = self.empty_segments = 0
        for segment, text in zip(data["segments"], lines):
            old_text = segment.get("target") or ""
            if not text.strip():
                self.empty_segments += 1
            elif old_text != text:
                segment["target"] = text
                self.changed_by_user += 1
            else:
                self.unchanged_segments += 1
        self.write_json(json_file, data)
        print(f"TXT -> JSON: segments changed by user: {self.changed_by_user}, unchanged segments {self.unchanged_segments}, empty segments {self.empty_segments} / total {len(data['segments'])}")
        return self.changed_by_user

    def import_txt_to_sdlxliff(self, txt_file, json_file, sdlxliff_file, output_file):
        self.import_txt_to_json(txt_file, json_file)
        return self.import_to_sdlxliff(sdlxliff_file, json_file, output_file)