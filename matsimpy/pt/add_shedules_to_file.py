import xml.etree.ElementTree as ET
import gzip
import logging

logging.basicConfig(level=logging.INFO)

# Load the base XML
logging.info("loading base file: transitSchedule.xml.gz")
with gzip.open("../../input/_pt/berlin-v6.4-transitSchedule.xml.gz", "rt", encoding="utf-8") as f:
    tree_base = ET.parse(f)
root_base = tree_base.getroot()

# --- Drop transitLine elements with id starting with a custom prefix ---
logging.info("Removing old versions")
for drop_line_name in ["S2-", "S8-", "S75-"]:
    for line in list(root_base.findall("transitLine")):
        if line.get("id", "").startswith(drop_line_name):
            root_base.remove(line)
            logging.info("removed line: id=%s", line.get("id"))

# Load the extra XML
logging.info("loading replacement lines")
tree_extra = ET.parse("replace_schedule.xml")
root_extra = tree_extra.getroot()

# Append all <transitLine> elements from extra into base
logging.info("adding replacement lines")
for line in root_extra.findall("transitLine"):
    root_base.append(line)

# Save merged XML
logging.info("saving scenario file: transitSchedule.xml.gz")
with gzip.open("../../input/_pt/scenario_berlin-v6.4-transitSchedule.xml.gz", "wb") as f:
    tree_base.write(f, encoding="utf-8", xml_declaration=True)

