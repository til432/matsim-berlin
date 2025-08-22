import xml.etree.ElementTree as ET
import gzip
import logging

logging.basicConfig(level=logging.INFO)

def save_gzip_xml(tree, filename, doctype=None):
    # Serialize root element only
    xml_body = ET.tostring(tree.getroot(), encoding="utf-8").decode("utf-8")

    # Build header + optional DOCTYPE + body
    xml_header = "<?xml version='1.0' encoding='utf-8'?>\n"
    if doctype:
        xml_output = xml_header + doctype + xml_body
    else:
        xml_output = xml_header + xml_body

    # Write as text, not bytes
    with gzip.open(filename, "wt", encoding="utf-8") as f:
        f.write(xml_output)

def strip_ns(elem):
    """Remove namespace prefixes recursively."""
    for e in elem.iter():
        if '}' in e.tag:
            e.tag = e.tag.split('}', 1)[1]  # remove namespace
    return elem

# Load the base XML
logging.info("loading base file: transitVehicles.xml.gz")
with gzip.open("../../input/v6.4/_pt/berlin-v6.4-transitVehicles.xml.gz", "rt", encoding="utf-8") as f:
    tree_base = ET.parse(f)
root_base = tree_base.getroot()

# Load the extra XML
logging.info("loading replacement vehicles")
tree_extra = ET.parse("replace_vehicles.xml")
root_extra = tree_extra.getroot()

# Append all <vehicle> elements from extra into base
logging.info("adding vehicles")
for vehicle in root_extra.findall(".//vehicle"):  # find all <vehicle> anywhere in extra
    strip_ns(vehicle)
    root_base.append(vehicle)

# Also strip base root if needed
strip_ns(root_base)

# Save merged XML
doctype = "<!DOCTYPE transitVehicles SYSTEM 'https://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd'>\n"
logging.info("saving scenario file: transitVehicles.xml.gz")
save_gzip_xml(tree_base, "../../input/v6.4/_pt/scenario_berlin-v6.4-transitVehicles.xml.gz", doctype=doctype)
