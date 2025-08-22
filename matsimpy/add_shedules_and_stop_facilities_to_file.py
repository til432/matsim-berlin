import xml.etree.ElementTree as ET
import gzip
import logging

logging.basicConfig(level=logging.INFO)

def save_gzip_xml(tree, filename, doctype=None):
    # Convert tree to string (without XML declaration first)
    xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8")

    # Build final XML string with XML declaration + optional DOCTYPE
    xml_header = b"<?xml version='1.0' encoding='utf-8'?>\n"
    if doctype:
        xml_bytes = xml_header + doctype.encode("utf-8") + xml_bytes
    else:
        xml_bytes = xml_header + xml_bytes

    with gzip.open(filename, "wb") as f:
        f.write(xml_bytes)


# Load the base XML
logging.info("loading base file: transitSchedule.xml.gz")
with gzip.open("../input/v6.4/_pt/berlin-v6.4-transitSchedule.xml.gz", "rt", encoding="utf-8") as f:
    tree_base = ET.parse(f)
root_base = tree_base.getroot()

# --- Drop transitLine elements with id starting with a custom prefix ---
logging.info("Removing old versions")
for drop_line_name in ["S2-", "S8-", "S75-"]:
    for line in list(root_base.findall("transitLine")):
        if line.get("id", "").startswith(drop_line_name):
            root_base.remove(line)
            logging.info("removed line: id=%s", line.get("id"))

# Load the extra XML schedule
logging.info("loading replacement lines")
tree_extra = ET.parse("pt/replace_schedule.xml")
root_extra = tree_extra.getroot()

# Append all <transitLine> elements from extra into base
logging.info("adding replacement lines")
for line in root_extra.findall("transitLine"):
    root_base.append(line)

# Load the extra stop facilities
logging.info("loading new stops")
tree_extra = ET.parse("network/stop_facilities.xml")
root_extra = tree_extra.getroot()

# Find the <transitStops> element in the base schedule, or create if missing
transit_stops_base = root_base.find("transitStops")

# Append new stopFacilities
for stop in root_extra.findall(".//stopFacility"):
    transit_stops_base.append(stop)
    logging.info("added stop: id=%s", stop.get("id"))

# Save merged XML
logging.info("saving scenario file: transitSchedule.xml.gz")

# Preserve DOCTYPE if needed
doctype = '<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n'

save_gzip_xml(tree_base,"../input/v6.4/_pt/scenario_berlin-v6.4-transitSchedule.xml.gz", doctype=doctype)

