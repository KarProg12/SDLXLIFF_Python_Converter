# Co robi ten plik?
# 1. Czyta plik .sdlxliff i zapisuje segmenty do export.json
# 2. Czyta export.json i wstawia tlumaczenia z powrotem do .sdlxliff
# 3. Zamienia JSON na 2 pliki TXT i z powrotem
# Uzywamy tylko: funkcje, listy, slowniki, for, if, open(), json, try/except

import json
import xml.etree.ElementTree as ET

# To sa "nazwiska" tagow w pliku XML. Python potrzebuje ich, zeby znalezc tagi.
# Nie musisz ich rozumiec na pamiec - po prostu kopiuj je tak jak sa.
NAMESPACES = {
    "sdl": "http://sdl.com/FileTypes/SdlXliff/1.0",
    "xliff": "urn:oasis:names:tc:xliff:document:1.2",
}
XLIFF = "{urn:oasis:names:tc:xliff:document:1.2}"

# Te statusy znacza: "juz przetlumaczone, nie ruszaj"
TRANSLATED_STATUSES = ["Translated", "ApprovedTranslation", "ApprovedSignOff"]


def tekst_z_elementu(element):
    """Bierze tekst z elementu XML razem z tagami w srodku, np. <g>.
    Przyklad: Hello <g>world</g> -> "Hello <g>world</g>"
    """
    if element is None:
        return ""

    # Zbieramy kawalki tekstu do jednej listy, na koncu je laczymy.
    kawalki = []

    # Tekst przed pierwszym tagiem w srodku
    if element.text:
        kawalki.append(element.text)

    # Dla kazdego tagu w srodku...
    for dziecko in element:
        if dziecko.tag.startswith("{http://sdl.com/FileTypes/SdlXliff/1.0}"):
            nazwa = "sdl:" + dziecko.tag.split("}", 1)[-1]
        elif dziecko.tag.startswith("{"):
            nazwa = dziecko.tag.split("}", 1)[-1]
        else:
            nazwa = dziecko.tag

        # Atrybuty tagu, np. id="1"
        atrybuty = ""
        for nazwa_atr, wartosc in dziecko.attrib.items():
            if nazwa_atr.startswith("{http://www.w3.org/XML/1998/namespace}"):
                nazwa_atr = "xml:" + nazwa_atr.split("}", 1)[-1]
            elif nazwa_atr.startswith("{"):
                nazwa_atr = nazwa_atr.split("}", 1)[-1]

            bezpieczna = wartosc.replace("&", "&amp;").replace('"', "&quot;")
            atrybuty = atrybuty + " " + nazwa_atr + '="' + bezpieczna + '"'

        # Tekst w srodku tagu (funkcja wywoluje sama siebie - rekurencja)
        srodek = tekst_z_elementu(dziecko)

        if srodek:
            kawalki.append("<" + nazwa + atrybuty + ">" + srodek + "</" + nazwa + ">")
        else:
            kawalki.append("<" + nazwa + atrybuty + "/>")

        # Tekst PO tym tagu
        if dziecko.tail:
            kawalki.append(dziecko.tail)

    return "".join(kawalki)


def daj_przestrzen_nazw(element):
    """AI czasem zwraca zwykly <g>, a Trados chce <g> z przestrzenia nazw.
    Ta funkcja dopisuje ja do kazdego zwyklego tagu.
    """
    for dziecko in element:
        if not dziecko.tag.startswith("{"):
            dziecko.tag = XLIFF + dziecko.tag
        daj_przestrzen_nazw(dziecko)


def eksportuj_do_json(plik_sdlxliff, folder_wyjsciowy):
    """Czyta .sdlxliff i zapisuje export.json w podanym folderze."""
    import os

    segmenty = []
    # Czytami plik XML po jednym trans-unit
    for _, jednostka in ET.iterparse(plik_sdlxliff, events=('end',)):
        if not jednostka.tag.endswith("}trans-unit"):
            continue

        zrodlo = jednostka.find("xliff:seg-source", NAMESPACES)
        definicje = jednostka.find("sdl:seg-defs", NAMESPACES)
        cel = jednostka.find("xliff:target", NAMESPACES)

        if zrodlo is None or definicje is None:
            jednostka.clear()
            continue

        statusy = {}
        for definicja in definicje.findall("sdl:seg", NAMESPACES):
            statusy[definicja.get("id")] = [definicja.get("conf"), definicja.get("locked")]

        stare_tlumaczenia = {}
        if cel is not None:
            for znacznik in cel.findall(".//xliff:mrk", NAMESPACES):
                if znacznik.get("mtype") == "seg":
                    stare_tlumaczenia[znacznik.get("mid")] = tekst_z_elementu(znacznik)


        for znacznik in zrodlo.findall(".//xliff:mrk", NAMESPACES):
            if znacznik.get("mtype") != "seg":
                continue

            seg_id = znacznik.get("mid")
            if seg_id not in statusy:
                continue

            status, zablokowany = statusy[seg_id]

            if zablokowany == "true" or status in TRANSLATED_STATUSES:
                continue

            segmenty.append({
                "trans-unit_id": jednostka.get("id"),
                "seg_id": seg_id,
                "status": status or "Not Translated",
                "source": tekst_z_elementu(znacznik),
                "target": stare_tlumaczenia.get(seg_id, "")
                })

        jednostka.clear()

    # Zapisujemy do pliku JSON
    os.makedirs(folder_wyjsciowy, exist_ok=True)
    sciezka = os.path.join(folder_wyjsciowy, "export.json")
    with open(sciezka, "w", encoding="utf-8") as plik:
        json.dump({"segments": segmenty}, plik, ensure_ascii=False, indent=2)

    print("Gotowe! Wyeksportowano", len(segmenty), "segmentow.")
    return len(segmenty)

def importuj_do_sdlxliff(plik_sdlxliff, plik_json, plik_wyjsciowy):
    """Wstawia tlumaczenia z JSON z powrotem do pliku .sdlxliff."""
    import shutil
    import os

    if plik_wyjsciowy == plik_sdlxliff:
        print("NIE ZAPISANO: plik wyjściowy to ten sam plik co wejściowy!")
        return 0

    if not os.path.exists(plik_sdlxliff + ".bak"):
        shutil.copy(plik_sdlxliff, plik_sdlxliff + ".bak")

    with open(plik_json, encoding="utf-8") as plik:
        dane = json.load(plik)

    # Slownik: (id_jednostki, id_segmentu) -> tlumaczenie
    tlumaczenia = {}
    for segment in dane["segments"]:
        tekst = segment.get("target", "").strip()
        if tekst:
            klucz = (str(segment["trans-unit_id"]), str(segment["seg_id"]))
            tlumaczenia[klucz] = tekst

    drzewo = ET.parse(plik_sdlxliff)
    korzen = drzewo.getroot()

    wstawiono = 0
    pominieto = 0

    for jednostka in korzen.findall(".//xliff:trans-unit", NAMESPACES):
        jednostka_id = str(jednostka.get("id"))
        cel = jednostka.find("xliff:target", NAMESPACES)
        definicje = jednostka.find("sdl:seg-defs", NAMESPACES)
        zrodlo = jednostka.find("xliff:seg-source", NAMESPACES)

        if cel is None or definicje is None:
            pominieto += 1
            continue

        # Znajdz istniejace znaczniki <mrk> w celu: id -> element
        znaczniki = {}
        for znacznik in cel.findall(".//xliff:mrk", NAMESPACES):
            if znacznik.get("mtype") == "seg":
                znaczniki[znacznik.get("mid")] = znacznik

        zrodla = {}
        if zrodlo is not None:
            for znacznik in zrodlo.findall(".//xliff:mrk", NAMESPACES):
                if znacznik.get("mtype") == "seg":
                    zrodla[znacznik.get("mid")] = tekst_z_elementu(znacznik)

        for definicja in definicje.findall("sdl:seg", NAMESPACES):
            seg_id = definicja.get("id")
            klucz = (jednostka_id, seg_id)

            if klucz not in tlumaczenia:
                continue

            # Jesli nie ma znacznika w celu, tworzymy nowy
            if seg_id not in znaczniki:
                nowy = ET.SubElement(cel, XLIFF + "mrk")
                nowy.set("mtype", "seg")
                nowy.set("mid", seg_id)
                znaczniki[seg_id] = nowy

            znacznik = znaczniki[seg_id]
            nowy_tekst = tlumaczenia[klucz]

            zrodlo_tekst = zrodla.get(seg_id, "")
            if zrodlo_tekst.count("<") != nowy_tekst.count("<"):
                print(f"UWAGA: inna liczba tagów w segmencie {seg_id}")
                print(f"Źródło: {zrodlo_tekst}")
                print(f"Tłumaczenie: {nowy_tekst}")

            # Czyscimy stary tekst, ale zachowujemy atrybuty
            stare_atrybuty = dict(znacznik.attrib)
            stary_tail = znacznik.tail
            znacznik.clear()

            for nazwa, wartosc in stare_atrybuty.items():
                znacznik.set(nazwa, wartosc)
            znacznik.set("mtype", "seg")
            znacznik.set("mid", seg_id)
            znacznik.tail = stary_tail

            # Probujemy wstawic tekst z tagami jako XML.
            # Jesli sie nie uda (np. zwykly znak &), wstawiamy jako zwykly tekst.
            try:
                opakowanie = '<wrap xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:sdl="http://sdl.com/FileTypes/SdlXliff/1.0">' + nowy_tekst + "</wrap>"
                fragment = ET.fromstring(opakowanie)
                daj_przestrzen_nazw(fragment)
                znacznik.text = fragment.text
                for dziecko in fragment:
                    znacznik.append(dziecko)
            except ET.ParseError:
                znacznik.text = nowy_tekst

            definicja.set("conf", "Draft")
            wstawiono += 1

    # Rejestrujemy przestrzenie nazw, zeby plik wygladal ladnie
    ET.register_namespace("sdl", "http://sdl.com/FileTypes/SdlXliff/1.0")
    ET.register_namespace("", "urn:oasis:names:tc:xliff:document:1.2")
    drzewo.write(plik_wyjsciowy, encoding="utf-8", xml_declaration=True)

    print(f"{wstawiono=}")
    print(f"{pominieto=}")
    print(f"Razem tłumaczeń było -> {len(tlumaczenia)} <- tłumaczeń")

    return wstawiono


def eksportuj_json_do_txt(plik_json, folder_wyjsciowy):
    """JSON -> 2 pliki TXT: jeden tylko do czytania, drugi do tlumaczenia."""
    import os

    with open(plik_json, encoding="utf-8") as plik:
        dane = json.load(plik)

    nazwa = os.path.splitext(os.path.basename(plik_json))[0]
    os.makedirs(folder_wyjsciowy, exist_ok=True)

    sciezka_zrodlo = os.path.join(folder_wyjsciowy, nazwa + "_source.txt")
    sciezka_cel = os.path.join(folder_wyjsciowy, nazwa + "_target.txt")

    with open(sciezka_zrodlo, "w", encoding="utf-8") as plik_zrodlo:
        with open(sciezka_cel, "w", encoding="utf-8") as plik_cel:
            for segment in dane["segments"]:
                zrodlo_jedna_linia = segment["source"].replace("\n", "\\n")
                plik_zrodlo.write(zrodlo_jedna_linia + "\n")

                cel_jedna_linia = (segment.get("target") or "").replace("\n", "\\n")
                plik_cel.write(cel_jedna_linia + "\n")

    print("TXT gotowe.")
    return len(dane["segments"])


def importuj_txt_do_json(plik_txt, plik_json):
    """Czyta przetlumaczony TXT i wstawia tlumaczenia z powrotem do JSON."""
    with open(plik_json, encoding="utf-8") as plik:
        dane = json.load(plik)

    linie = []
    with open(plik_txt, encoding="utf-8") as plik:
        for linia in plik:
            linie.append(linia.rstrip("\n").replace("\\n", "\n"))

        if len(linie) != len(dane["segments"]):
            print("BŁĄD: liczba linii w TXT nie pasuje do liczby segmentów!\n"
                  f"linie TXT: {len(linie)}\n"
                  f"segmenty JSON: {len(dane['segments'])}")
            return 0

    zaaktualizowano = 0
    for segment, tekst in zip(dane["segments"], linie):
        if tekst.strip():
            segment["target"] = tekst
            zaaktualizowano = zaaktualizowano + 1

    with open(plik_json, "w", encoding="utf-8") as plik:
        json.dump(dane, plik, ensure_ascii=False, indent=2)

    print(f"TXT -> JSON: zaaktualizowano {zaaktualizowano} segmentów.")
    return zaaktualizowano