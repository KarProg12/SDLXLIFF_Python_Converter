# SDLXLIFF <-> JSON converter.
# Preserves every inline tag: full tag name, every attribute, namespace and tail text.
import os.path
import xml.etree.ElementTree as ET
import json
from xml.sax.saxutils import quoteattr

# Namespace declarations kept when the file is saved, so prefixes stay readable.
ET.register_namespace('sdl', "http://sdl.com/FileTypes/SdlXliff/1.0")
ET.register_namespace('', "urn:oasis:names:tc:xliff:document:1.2")

# Namespace URIs used in every lookup. Keys are the prefixes used in find() calls.
NAMESPACES = {
    "sdl": "http://sdl.com/FileTypes/SdlXliff/1.0",
    "xliff": "urn:oasis:names:tc:xliff:document:1.2",
}
XLIFF_NAMESPACE = "urn:oasis:names:tc:xliff:document:1.2"
SDL_NAMESPACE = "http://sdl.com/FileTypes/SdlXliff/1.0"

# Translation statuses that mean "already done" - such segments are never exported.
COMPLETED_STATUSES = ['Translated', 'ApprovedTranslation', 'ApprovedSignOff']


def local_tag_name(full_tag_name):
    # Strips the "{namespace}" prefix, so "{urn:...}g" becomes "g".
    return full_tag_name.split('}', 1)[-1]


def serialise_element_to_text(element):
    # Turns one XML element (and everything inside it) into the text format
    # used in JSON, for example: Hello <g id='1' ctype='bold'>world</g>!
    # Every attribute is kept, not just id, and tail text is kept too.
    text_parts = []
    if element.text:
        # Text before the first child element.
        text_parts.append(element.text)
    for child_element in element:
        tag_name = local_tag_name(child_element.tag)
        # All attributes of this tag, each value safely quoted.
        # ElementTree stores attributes in .attrib.
        attributes_text = "".join(f" {name}={quoteattr(value)}" for name, value in child_element.attrib.items())
        inner_text = serialise_element_to_text(child_element)
        if inner_text:
            # Tag with content: <g ...>content</g>
            text_parts.append(f"<{tag_name}{attributes_text}>{inner_text}</{tag_name}>")
        else:
            # Empty tag: <x .../>
            text_parts.append(f"<{tag_name}{attributes_text}/>")
        if child_element.tail:
            # Text after this tag, before the next tag or the end of the parent.
            text_parts.append(child_element.tail)
    return ''.join(text_parts)


def extract_segment_text(element):
    # Returns the readable text of one <mrk> segment, with inline tags kept.
    # Kept as a small wrapper so the rest of the code reads clearly.
    if element is None:
        return ''
    return serialise_element_to_text(element)


def restore_namespaces(element, xliff_namespace=XLIFF_NAMESPACE):
    # Gives every plain tag (for example <g> returned by AI) the XLIFF namespace,
    # so Trados reads it as an inline tag. Tags that already have a namespace
    # (for example <sdl:...>) are left untouched.
    for child_element in element:
        if not child_element.tag.startswith('{'):
            child_element.tag = f"{{{xliff_namespace}}}{child_element.tag}"
        restore_namespaces(child_element, xliff_namespace)


def filter_terminology(segments_data, termbase):
    # Keeps only the terms that really occur in the source text,
    # so the AI prompt stays short. Checked segment by segment, no giant copy of all text.
    if not termbase:
        return {'required_terms': {}, 'forbidden_terms': []}
    matched_required_terms = {}
    matched_forbidden_terms = []
    for segment in segments_data:
        source_text_lowercase = segment['source'].lower()
        for source_term, target_term in termbase.get('required', {}).items():
            if source_term.lower() in source_text_lowercase:
                matched_required_terms[source_term] = target_term
        for forbidden_word in termbase.get('forbidden', []):
            if forbidden_word.lower() in source_text_lowercase and forbidden_word not in matched_forbidden_terms:
                matched_forbidden_terms.append(forbidden_word)
    return {"required_terms": matched_required_terms, "forbidden_terms": matched_forbidden_terms}


def export_sdlxliff_to_json(original_sdlxliff_path, output_folder_path, termbase=None):
    # Reads SDLXLIFF segment by segment (iterparse) and writes export.json.
    # Only segments that are not locked and not already translated are exported.
    segments_data = []
    # iterparse with 'end' events: one finished <trans-unit> at a time, freed after use.
    for _, trans_unit in ET.iterparse(original_sdlxliff_path, events=('end',)):
        if not trans_unit.tag.endswith('}trans-unit'):
            continue
        segment_source = trans_unit.find('xliff:seg-source', NAMESPACES)
        segment_definitions = trans_unit.find('sdl:seg-defs', NAMESPACES)
        target_element = trans_unit.find('xliff:target', NAMESPACES)
        if segment_source is not None and segment_definitions is not None:
            # Segment id -> [confirmation status, locked flag]
            segment_status_by_id = {
                definition.get('id'): [definition.get('conf'), definition.get('locked')]
                for definition in segment_definitions.findall('sdl:seg', NAMESPACES)
            }
            # Segment id -> current target text, kept if a translation already exists.
            target_text_by_segment_id = {}
            if target_element is not None:
                for target_marker in target_element.findall('.//xliff:mrk', NAMESPACES):
                    if target_marker.get('mtype') == 'seg':
                        target_text_by_segment_id[target_marker.get('mid')] = extract_segment_text(target_marker)
            for source_marker in segment_source.findall('.//xliff:mrk', NAMESPACES):
                if source_marker.get('mtype') != 'seg':
                    continue
                segment_id = source_marker.get('mid')
                segment_status = segment_status_by_id.get(segment_id)
                if segment_status is None:
                    # No entry in seg-defs: skip this segment, do not crash the whole export.
                    continue
                confirmation_status, locked_flag = segment_status
                if locked_flag == 'true' or confirmation_status in COMPLETED_STATUSES:
                    continue
                segments_data.append({
                    'trans-unit_id': trans_unit.get('id'),
                    'seg_id': segment_id,
                    'status': confirmation_status or "Not Translated",
                    'source': extract_segment_text(source_marker),
                    'target': target_text_by_segment_id.get(segment_id, ""),
                    'ai_translation': '',
                    'ai_comment': ""
                })
        # Free the processed unit, so memory does not grow with file size.
        trans_unit.clear()
    payload = {"terminology": filter_terminology(segments_data, termbase), "segments": segments_data}
    os.makedirs(output_folder_path, exist_ok=True)
    with open(os.path.join(output_folder_path, 'export.json'), 'w', encoding='utf-8') as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)
    print(f"\nDone!\n Exported {len(segments_data)} segments.")
    return len(segments_data)  # Segment count, shown in the success messagebox.


def parse_translation_fragment(translation_text):
    # Parses AI translation text (which may contain inline tags) into XML.
    # The wrapper declares both namespaces, so <g> and <sdl:...> both parse.
    # Plain tags get the XLIFF namespace afterward, namespaced tags keep theirs.
    wrapper = (
        f"<wrap xmlns=\"{XLIFF_NAMESPACE}\" xmlns:sdl=\"{SDL_NAMESPACE}\">"
        f"{translation_text}</wrap>"
    )
    fragment = ET.fromstring(wrapper)
    restore_namespaces(fragment)
    return fragment


def import_to_sdlxliff(original_sdlxliff_path, translated_json_path, output_sdlxliff_path):
    # Writes ai_translation values from JSON back into a copy of the SDLXLIFF file.
    with open(translated_json_path, 'r', encoding='utf-8') as input_file:
        json_data = json.load(input_file)
    # (trans-unit id, segment id) -> AI translation, only non-empty translations.
    # IDs are normalised to str: JSON may hold 1, XML always holds "1". Without this, nothing matches.
    translations_by_key = {
        (str(segment['trans-unit_id']), str(segment['seg_id'])): segment.get('ai_translation', '').strip()
        for segment in json_data['segments']
        if segment.get('ai_translation', '').strip()
    }
    # iterparse with 'start' to grab the root, 'end' to process each finished unit.
    event_iterator = ET.iterparse(original_sdlxliff_path, events=('start', 'end'))
    _, sdlxliff_root = next(event_iterator)
    skipped_translations = []
    inserted_count = 0  # Counted only when a translation is really written into a <mrk>.
    for event_name, trans_unit in event_iterator:
        if event_name != 'end' or not trans_unit.tag.endswith('}trans-unit'):
            continue
        trans_unit_id = str(trans_unit.get('id'))  # str() to match the normalised JSON keys.
        target_element = trans_unit.find('xliff:target', NAMESPACES)
        segment_definitions = trans_unit.find('sdl:seg-defs', NAMESPACES)
        if target_element is None or segment_definitions is None:
            # Nowhere to write: remember these translations and report them at the end.
            skipped_translations += [key for key in translations_by_key if key[0] == trans_unit_id]
            continue
        # Segment id -> existing <mrk> element in the target.
        target_markers_by_id = {
            marker.get('mid'): marker
            for marker in target_element.findall('.//xliff:mrk', NAMESPACES)
            if marker.get('mtype') == 'seg'
        }
        for segment_definition in segment_definitions.findall('sdl:seg', NAMESPACES):
            segment_id = segment_definition.get('id')
            translation_key = (trans_unit_id, segment_id)
            if translation_key not in translations_by_key:
                continue
            if segment_id not in target_markers_by_id:
                # Never-translated segment has no <mrk> yet: create it instead of dropping the translation.
                marker_element = ET.SubElement(target_element, f"{{{XLIFF_NAMESPACE}}}mrk")
                marker_element.set('mtype', 'seg')
                marker_element.set('mid', segment_id)
                target_markers_by_id[segment_id] = marker_element
            marker_element = target_markers_by_id[segment_id]
            new_translation_text = translations_by_key[translation_key]
            # Save everything the old <mrk> had, so clear() does not lose it.
            preserved_attributes = dict(marker_element.attrib)
            preserved_tail_text = marker_element.tail
            marker_element.clear()
            # Restore all original attributes, then make sure seg identity is set.
            for attribute_name, attribute_value in preserved_attributes.items():
                marker_element.set(attribute_name, attribute_value)
            marker_element.set('mtype', 'seg')
            marker_element.set('mid', segment_id)
            marker_element.tail = preserved_tail_text
            try:
                # Translation with inline tags: parse it and move the tags into <mrk>.
                fragment = parse_translation_fragment(new_translation_text)
                marker_element.text = fragment.text
                for child_element in fragment:
                    marker_element.append(child_element)
                # Tail text of the last child belongs to the fragment, keep it on that child.
                # (ElementTree already keeps it on the child, nothing to do here.)
            except ET.ParseError:
                # Not valid XML (for example a bare & or < in plain text): save as plain text.
                # ElementTree escapes it correctly when the file is written.
                marker_element.text = new_translation_text
            segment_definition.set('conf', 'Draft')
            inserted_count += 1
    ET.ElementTree(sdlxliff_root).write(output_sdlxliff_path, encoding='utf-8', xml_declaration=True)
    print(f"\nThe import was successful. Skipped: {len(skipped_translations)}")
    if skipped_translations:
        print("Skipped:", skipped_translations)
    return inserted_count, len(skipped_translations)  # (inserted, skipped) for the messagebox.




# [STRIPPED 75 bytes]
# TXT export / import - plain .txt files, easy to edit in Notepad.
# Workflow: export.json -> 2 TXT files -> edit TRANSLATION: lines -> TXT back to JSON -> normal import to SDLXLIFF.
# One segment = one block. The [ID: trans-unit|seg] line is the key: do not delete it.
# Example block:
#   ==============================
#   [ID: 12|3]
#   SOURCE: Hello <g id="1">world</g>
#   TRANSLATION:
#   Witaj <g id="1">swiecie</g>
# [STRIPPED 75 bytes]

def export_json_to_txt_files(export_json_path, output_folder_path):
    # JSON -> 2 TXT files: read-only source file + file to translate.
    with open(export_json_path, encoding='utf-8') as input_file:
        json_data = json.load(input_file)
    base_name = os.path.splitext(os.path.basename(export_json_path))[0]
    source_txt_path = os.path.join(output_folder_path, f"{base_name}_source.txt")
    translate_txt_path = os.path.join(output_folder_path, f"{base_name}_translate.txt")
    os.makedirs(output_folder_path, exist_ok=True)
    with open(source_txt_path, 'w', encoding='utf-8') as source_file, \
         open(translate_txt_path, 'w', encoding='utf-8') as translate_file:
        source_file.write("DO NOT EDIT - source text only\n\n")
        translate_file.write("EDIT THIS FILE - write translation under TRANSLATION:, do not delete [ID:] lines\n\n")
        for segment in json_data['segments']:
            segment_key = f"{segment['trans-unit_id']}|{segment['seg_id']}"
            source_file.write(f"==============================\n[ID: {segment_key}]\nSOURCE: {segment['source']}\n\n")
            existing_translation = segment.get('ai_translation') or segment.get('target') or ''
            translate_file.write(f"==============================\n[ID: {segment_key}]\nSOURCE: {segment['source']}\nTRANSLATION:\n{existing_translation}\n\n")
    print(f"TXT exported: {source_txt_path} + {translate_txt_path}")
    return len(json_data['segments'])


def import_txt_files_to_json(translate_txt_path, export_json_path):
    # TXT edited by hand -> back into JSON. Only ai_translation changes, rest of JSON untouched.
    with open(export_json_path, encoding='utf-8') as input_file:
        json_data = json.load(input_file)
    translations_by_key = {}
    current_key, inside_translation, current_lines = None, False, []
    with open(translate_txt_path, encoding='utf-8') as translate_file:
        for raw_line in translate_file:
            line = raw_line.rstrip("\n")
            if line.startswith("=============================="):
                if current_key is not None:
                    translations_by_key[current_key] = "\n".join(current_lines).strip()
                current_key, inside_translation, current_lines = None, False, []
            elif line.startswith("[ID:"):
                trans_unit_id, segment_id = line[len("[ID:"):-1].strip().split("|", 1)
                current_key = (trans_unit_id.strip(), segment_id.strip())
            elif line.startswith("TRANSLATION:"):
                inside_translation, current_lines = True, []
            elif line.startswith("SOURCE:"):
                inside_translation = False
            elif inside_translation and current_key is not None:
                current_lines.append(line)
    if current_key is not None:
        translations_by_key[current_key] = "\n".join(current_lines).strip()
    updated_count = 0
    for segment in json_data['segments']:
        segment_key = (str(segment['trans-unit_id']), str(segment['seg_id']))
        if segment_key in translations_by_key and translations_by_key[segment_key]:
            segment['ai_translation'] = translations_by_key[segment_key]
            updated_count += 1
    with open(export_json_path, 'w', encoding='utf-8') as output_file:
        json.dump(json_data, output_file, ensure_ascii=False, indent=2)
    print(f"TXT -> JSON: updated {updated_count} segment(s).")
    return updated_count