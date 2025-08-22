import pandas as pd
import xml.dom.minidom
import logging
logging.basicConfig(level=logging.INFO)


def minutes_to_hhmmss(total_minutes):
    total_minutes = int(total_minutes)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    seconds = 0
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def create_vehicle_list(vehicle_list):
    vehicle_output = "<vehicleDefinitions>"
    for vehicle in vehicle_list:
        vehicle_output += f'<vehicle id="{vehicle}" type="S-Bahn_veh_type"/>'
    vehicle_output += "</vehicleDefinitions>"
    return vehicle_output


def convert2xml(line):
    logging.info(f"Loading files for Line {line}")
    if line.endswith("_r"):
        backwards = True
    else:
        backwards = False

    freq = pd.read_csv("lines/frequency.csv", sep=";", encoding="cp1252")

    stations_links = pd.read_csv("stations_links.csv", sep=";", encoding="cp1252")

    stations = pd.read_csv(f"lines/{line.removesuffix('_r')}_line.csv", sep=";", encoding="cp1252", header=None)
    stations.rename(columns={0: "name"}, inplace=True)

    times = pd.read_csv(f"lines/{line.removesuffix('_r')}_times.csv", sep=";", encoding="cp1252")

    # Start and attributes
    output = f'<transitLine id="hw_{line}---1" name="{line}">'
    output = output + '<attributes>'
    output = output + '<attribute name="gtfs_agency_id" class="java.lang.String">401</attribute>'
    output = output + '<attribute name="gtfs_route_short_name" class="java.lang.String">S2</attribute>'
    output = output + '<attribute name="gtfs_route_type" class="java.lang.String">109</attribute>'
    output = output + '</attributes>'

    # transit routes
    filtered_freq = freq[freq["line"] == line]

    if backwards:
        logging.info(f"Adapting Input for backwards line")
        times = times.rename(columns={"from": "to", "to": "from", "backward": "forward", "forward": "backward"})
        stations = stations.iloc[::-1].reset_index(drop=True)
        stations = stations.rename(columns={"backward": "forward", "forward": "backward"})
        stations_links = stations_links.rename(columns={"backward": "forward", "forward": "backward"})
    stations = stations.merge(stations_links, on="name")

    n = 0
    vehicle_list = []
    for index_freq, row_freq in filtered_freq.iterrows():
        start = row_freq['start_hour']
        start_min = row_freq['start_min']
        end = row_freq['end_hour']
        freq_min = row_freq['freq_min']
        from_station = row_freq['from']
        to_station = row_freq['to']
        logging.info(f"Creating transit_route id=hw_{line}---1_{n} from {from_station} to {to_station}, "
                     f"beginning at {start:02}:{start_min:02}h until {end:02}:00h "
                     f"going every {freq_min:02} min")

        output = output + f'<transitRoute id="hw_{line}---1_{n}">'
        output = output + ('<attributes><attribute name="simple_route_type" class="java.lang.String">Suburban '
                           'Railway</attribute></attributes>')
        output = output + '<transportMode>Suburban Railway</transportMode>'
        output = output + '<routeProfile>'

        # iterate stops
        forwards_stations = stations.merge(times, left_on="name", right_on="to", how="left",
                                           suffixes=("_stations", "_times"))
        mask = False
        masks = []
        now = 0

        route = ""
        # route profile
        logging.info(f"Generating route for transit route id=hw_{line}---1_{n}")
        for index, row in forwards_stations.iterrows():
            if row['name'] == from_station:
                mask = True
                output = output + (f'<stop refId="{row["forward_stations"].removeprefix("pt_")}" arrivalOffset="00:00:00" '
                                   f'departureOffset="00:00:00" awaitDeparture="true"/>')
                route = route + f'<link refId="{row["forward_stations"]}"/><link refId="{row["forward_stations"]}-'
                continue

            masks.append(mask)
            if mask:
                output = output + (f'<stop refId="{row["forward_stations"].removeprefix("pt_")}" '
                                   f'arrivalOffset="{minutes_to_hhmmss(now + row["forward_times"])}" '
                                   f'departureOffset="{minutes_to_hhmmss(now + row["forward_times"])}" '
                                   f'awaitDeparture="true"/>')
                now = now + row['forward_times']

                if row['name'] == to_station:
                    route = route + f'{row["forward_stations"]}"/><link refId="{row["forward_stations"]}"/>'
                    mask = False
                else:
                    route = route + f'{row["forward_stations"]}"/><link refId="{row["forward_stations"]}"/><link refId="{row["forward_stations"]}-'

        output = output + '</routeProfile>'
        output = output + '<route>' + route + '</route>'

        # departures
        now_hour = start
        now_minute = start_min
        departures = ""
        departure_count = 0
        logging.info(f"Generating departures for transit route id=hw_{line}---1_{n}")
        departure_list = []
        while now_hour < end:
            departures = departures + (f'<departure id="{"hw_" + f"{line}---1_{n}_" + str(departure_count)}" '
                                       f'departureTime="{now_hour:02}:{now_minute:02}:00" '
                                       f'vehicleRefId="{"hw_veh_" + f"{line}---1_{n}_" + str(departure_count)}"/>')
            vehicle_list.append("hw_veh_" + f"{line}---1_{n}_" + str(departure_count))
            departure_list.append(f"{now_hour:02}:{now_minute:02}:00")
            now_minute = now_minute + freq_min
            # Time update
            if now_minute > 60:
                now_minute = now_minute - 60
                now_hour = now_hour + 1
            departure_count += 1
        output = output + '<departures>' + departures + '</departures>'
        logging.info(f"id=hw_{line}---1_{n} departs at {departure_list}")

        output = output + '</transitRoute>'
        n = n + 1

    output = output + '</transitLine>'
    # print(output)
    return output, vehicle_list


if __name__ == '__main__':
    lines = ["s2", "s2_r", "s8", "s8_r", "s75", "s75_r"]
    output_all_lines = ""
    all_vehicles = []
    for l in lines:
        add_output, vehicles = convert2xml(l)
        output_all_lines = output_all_lines + add_output
        all_vehicles.extend(vehicles)
    output_all_lines = '<transitSchedule>' + output_all_lines + '</transitSchedule>'
    logging.info("Creating replacement schedule xml-File")
    dom = xml.dom.minidom.parseString(output_all_lines)
    pretty_xml = dom.toprettyxml(indent="    ")  # 4 spaces per level

    # Save to file
    with open("replace_schedule.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    logging.info("Creating replacement vehicles xml-File")
    dom = xml.dom.minidom.parseString(create_vehicle_list(all_vehicles))
    pretty_xml = dom.toprettyxml(indent="    ")  # 4 spaces per level

    # Save to file
    with open("replace_vehicles.xml", "w", encoding="utf-8") as f:
        f.write(pretty_xml)

