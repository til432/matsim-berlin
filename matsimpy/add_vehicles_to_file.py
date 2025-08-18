import xml.etree.ElementTree as ET
import gzip
import logging

logging.basicConfig(level=logging.INFO)

# Load the base XML
logging.info("loading base file: transitVehicles.xml.gz")
with gzip.open("../input/_pt/berlin-v6.4-transitVehicles.xml.gz", "rt", encoding="utf-8") as f:
    tree_base = ET.parse(f)
root_base = tree_base.getroot()

# Load the extra XML
logging.info("loading replacement vehicles")
tree_extra = ET.parse("replace_vehicles.xml")
root_extra = tree_extra.getroot()

# Append all elements from extra into base
logging.info("adding vehicles")
for line in root_extra.findall("vehicle"):
    root_base.append(line)

# Save merged XML
logging.info("saving scenario file: transitVehicles.xml.gz")
with gzip.open("../input/_pt/scenario_berlin-v6.4-transitVehicles.xml.gz", "wb") as f:
    tree_base.write(f, encoding="utf-8", xml_declaration=True)

