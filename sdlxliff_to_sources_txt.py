import xml.etree.ElementTree as ET
from pathlib import Path

file_or_path_input = input("Enter the absolute path or if he file is in the same folder with program, enter only a filename:\n"
                           " >> ")
file_path = Path(file_or_path_input)

tree = ET.parse(file_path)
root = tree.getroot()

# auto namespace fetching from file with root.tag
# when splitting returns list ['{namespace', '}'] and index [0] deletes this curly bracket
# strip separates and removes the curly bracket at the beginning of the namespace
namespace = root.tag.split('}')[0].strip('{')
namespaces_map = {'xliff': namespace}

with open('sources.txt', 'w', encoding='UTF-8') as txt_file:
    for element in root.findall('.//xliff:source', namespaces_map):
        txt = "".join(element.itertext()).strip()

        if txt:
            txt_file.write(txt + "\n")

print("\nDone!")


