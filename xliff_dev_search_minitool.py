lazy import xml.etree.ElementTree as ET
from pathlib import Path

file_path = input("Enter the file name or absolute path if the file is not in the same directory with this program:\n >> ")
file_path = Path(file_path)

while True:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        xliff_namespace_address = "urn:oasis:names:tc:xliff:document:1.2"
        space_map = {"xliff": xliff_namespace_address}

        path_input = input("\n! ['.//' means 'search in all children (and also in children of those children) of the parent'] !\n"
                           f"Search in '{file_path}' file structure:\n"
                           f" >> .//xliff:")
        path = ".//xliff:" + path_input
        file = root.find(path, space_map)
        print()
        print(file)
        print(file.attrib)

    except FileNotFoundError, AttributeError, KeyboardInterrupt:
        if KeyboardInterrupt:
            print("\nEscaped the program")
            break

        elif FileNotFoundError:
            print(f"There's no file '{file_path}' or it is not a xml, xliff or sdlxliff file")
            continue

        elif AttributeError:
            print("Your query is probably not a parent or has no attribute like you typed\nCheck the file structure")
            continue