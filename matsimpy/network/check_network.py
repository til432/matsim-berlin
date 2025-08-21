import xml.etree.ElementTree as ET

# Load your MATSim network
tree = ET.parse('../berlin-v6.4-network-with-pt-bearb.xml')  # replace with your file
root = tree.getroot()

# Collect all node IDs
nodes = set()
for node in root.findall('nodes/node'):
    node_id = node.get('id')
    if node_id in nodes:
        print(f"Duplicate node ID: {node_id}")
    nodes.add(node_id)

# Check links
link_ids = set()
for link in root.findall('links/link'):
    link_id = link.get('id')
    if link_id in link_ids:
        print(f"Duplicate link ID: {link_id}")
    link_ids.add(link_id)

    # Check numeric attributes
    for attr in ['length', 'freespeed', 'capacity', 'permlanes']:
        val = link.get(attr)
        if val is None or val.strip() == '':
            print(f"Link {link_id} has empty {attr}")
        else:
            try:
                num = float(val)
                if num <= 0 and attr != 'freespeed':  # freespeed can be tiny like 0.1
                    print(f"Link {link_id} has non-positive {attr}: {num}")
            except ValueError:
                print(f"Link {link_id} has invalid {attr}: {val}")

    # Check from/to nodes exist
    for node_attr in ['from', 'to']:
        node_id = link.get(node_attr)
        if node_id not in nodes:
            print(f"Link {link_id} references missing node {node_id}")
