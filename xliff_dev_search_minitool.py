lazy import xml.etree.ElementTree as ET
from pathlib import Path

file_path = input("Enter the file name or absolute path if the file is not in the same directory with this program:\n >> ")
file_path = Path(file_path)

try:
    while True:

        tree = ET.parse(file_path)
        root = tree.getroot()

        namespace = root.tag.split('}')[0].strip('{')
        space_map = {"xliff": namespace}

        path_input = input(
            "\n! ['.//' means 'search in all children (and also in children of those children) of the parent'] !\n"
            f"Search in '{file_path}' file structure:\n"
            f" >> .//xliff:")
        path = ".//xliff:" + path_input
        file = root.find(path, space_map)
        print()
        print(file)
        print(file.attrib)

except FileNotFoundError, AttributeError, KeyboardInterrupt:
    if not file_path.exists():
        print("\nFile doesn't exist or the path is incorrect")

    elif FileNotFoundError:
        print(f"There's no file '{file_path}' or it is not a xml, xliff or sdlxliff file")

    elif AttributeError:
        print("Your query is probably not a parent or has no attribute like you typed\nCheck the file structure")