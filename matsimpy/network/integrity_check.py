import xml.etree.ElementTree as ET

# --- Load the network links ---
network_file = r"C:\Users\til43\IdeaProjects\matsim-berlin\input\v6.4\berlin-v6.4-network-with-pt_edited.xml"
network_tree = ET.parse(network_file)
network_root = network_tree.getroot()

# Extract all link IDs from the network
network_links = set()
for link in network_root.findall(".//link"):
    link_id = link.get("id")
    network_links.add(link_id)

print(f"Total links in network: {len(network_links)}")

# --- Load the transit schedule ---
schedule_file = r"C:\Users\til43\IdeaProjects\matsim-berlin\input\v6.4\_pt\scenario_berlin-v6.4-transitSchedule.xml"
schedule_tree = ET.parse(schedule_file)
schedule_root = schedule_tree.getroot()

# Go through each transitRoute
missing_links_report = {}

for transitLine in schedule_root.findall(".//transitLine"):
    line_id = transitLine.get("id")
    for transitRoute in transitLine.findall(".//transitRoute"):
        route_id = transitRoute.get("id")
        route_elem = transitRoute.find("route")
        if route_elem is None:
            continue
        missing_links = []
        for link_ref in route_elem.findall("link"):
            ref_id = link_ref.get("refId")
            if ref_id not in network_links:
                missing_links.append(ref_id)
        if missing_links:
            missing_links_report[f"{line_id}/{route_id}"] = missing_links

# --- Print report ---
if missing_links_report:
    print("Missing links detected:")
    for route_key, links in missing_links_report.items():
        print(f"{route_key}: {links}")
else:
    print("All links in transit schedules exist in the network.")
