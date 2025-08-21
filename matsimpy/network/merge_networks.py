import gzip
import xml.etree.ElementTree as ET


def load_gzip_xml(filename):
    with gzip.open(filename, "rt", encoding="utf-8") as f:
        tree = ET.parse(f)
    return tree


def save_gzip_xml(tree, filename, doctype=None):
    # Convert tree to string
    xml_str = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)

    if doctype:
        xml_str = doctype.encode("utf-8") + xml_str

    with gzip.open(filename, "wb") as f:
        f.write(xml_str)


# Load compressed XML files
tree_a = ET.parse("nodes_and_links.xml")
tree_b = load_gzip_xml(r"C:\Users\til43\IdeaProjects\matsim-berlin\input\v6.4\berlin-v6.4-network-with-pt.xml.gz")

root_a = tree_a.getroot()
root_b = tree_b.getroot()

# Merge nodes
nodes_a = root_a.find("nodes")
links_a = root_a.find("links")
nodes_b = root_b.find("nodes")
links_b = root_b.find("links")

for node in nodes_a:
    nodes_b.append(node)

for link in links_a:
    links_b.append(link)

# Optional: pretty-print (Python 3.9+)
ET.indent(tree_b, space="    ")

# Preserve DOCTYPE if needed
doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n'

# Save merged network as gzip
save_gzip_xml(tree_b,
              r"C:\Users\til43\IdeaProjects\matsim-berlin\input\v6.4\berlin-v6.4-network-with-pt_edited.xml.gz",
              doctype=doctype)
