import xml.etree.ElementTree as ET

# Path to your input file
input_file = "nodes_and_links.txt"
output_file = "nodes_and_links.xml"

# Read the content of the txt file
with open(input_file, "r", encoding="utf-8") as f:
    xml_string = f.read()

root = ET.fromstring(xml_string)

# Strip inner text of all empty elements
for elem in root.iter():
    if elem.text is not None and elem.text.strip() == "":
        elem.text = None

# Optional pretty print
ET.indent(root, space="    ")

# Convert to string with self-closing tags
pretty_xml = ET.tostring(
    root,
    encoding="unicode",
    xml_declaration=True,
    short_empty_elements=True
)

# Save result
with open(output_file, "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print(f"Pretty XML has been saved to {output_file}")
