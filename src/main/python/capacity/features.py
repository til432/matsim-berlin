#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from argparse import ArgumentParser
from collections import defaultdict

import lxml.etree as ET
import pandas as pd
from shapely.geometry import LineString


def build_datasets(network, inter, routes):
    """ Build all datasets needed for training models"""
    ft = pd.read_csv(network)

    df_i = pd.read_csv(inter)
    df_i = pd.merge(df_i, ft, left_on="fromEdgeId", right_on="edgeId")

    df_r = pd.read_csv(routes).drop(columns=["speed"])
    df_r = pd.merge(df_r, ft, left_on="edgeId", right_on="edgeId")

    result = {}

    aggr = df_r.groupby(["junctionType"])
    for g in aggr.groups:
        result["speedRelative_" + str(g)] = prepare_dataframe(aggr.get_group(g), target="speedRelative")

    aggr = df_i.groupby(["junctionType"])
    df_i["norm_cap"] = df_i.capacity / df_i.numLanes
    for g in aggr.groups:
        result["capacity_" + str(g)] = prepare_dataframe(aggr.get_group(g), target="norm_cap")

    return result


def prepare_dataframe(df, target):
    """ Simple preprocessing """

    df = df.rename(columns={target: "target"})

    # Drop length outliers
    df = df[df.length < 500]

    # drop 2.5% smallest and largest
    drop = len(df) // 40
    df = df.drop(df.nsmallest(drop, ["target"]).index)
    df = df.drop(df.nlargest(drop, ["target"]).index)

    s = df['target']
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    iqr_lower = q1 - 1.5 * iqr
    iqr_upper = q3 + 1.5 * iqr
    outliers = s[(s < iqr_lower) | (s > iqr_upper)]

    df = df.drop(outliers.index)

    # remove unneeded features
    df = df[["target", "length", "speed",
             "dir_l", "dir_r", "dir_s",
             "priority_lower", "priority_equal", "priority_higher",
             "numFoes", "numLanes", "junctionSize"]]

    return df


def parse_ls(el):
    shape = el.attrib['shape']
    coords = [tuple(map(float, l.split(","))) for l in shape.split(" ")]
    return LineString(coords)


def combine_bitset(a, b):
    return "".join("1" if x[0] == "1" or x[1] == "1" else "0" for x in zip(a, b))


def read_network(sumo_network):
    """ Read sumo network from xml file. """

    edges = {}
    junctions = {}

    to_edges = defaultdict(lambda: [])

    # Aggregated connections, for outgoing edge
    connections = {}

    # count the indices of connections, assuming they are ordered
    # this seems to be the case according to sumo doc. there is no further index attribute
    idx = {}

    data_conns = []

    for _, elem in ET.iterparse(sumo_network, events=("end",),
                                tag=('edge', 'junction', 'connection'),
                                remove_blank_text=True):

        if elem.tag == "edge":
            edges[elem.attrib["id"]] = elem
            to_edges[elem.attrib["to"]].append(elem)
            continue

        elif elem.tag == "junction":
            junctions[elem.attrib["id"]] = elem
            idx[elem.attrib["id"]] = 0
            continue

        if elem.tag != "connection":
            continue

        # Rest is parsing connection        
        conn = elem.attrib

        fromEdge = edges[conn["from"]]
        fromLane = fromEdge.find("lane", {"index": conn["fromLane"]})

        toEdge = edges[conn["to"]]
        toLane = toEdge.find("lane", {"index": conn["toLane"]})

        junction = junctions[fromEdge.attrib["to"]]
        request = junction.find("request", {"index": str(idx[fromEdge.attrib["to"]])})

        # increase request index
        idx[fromEdge.attrib["to"]] += 1

        from_edge_id = fromEdge.attrib["id"]

        # Remove turn directions, which are not so relevant
        if conn["dir"] == "t":
            conn["dir"] = ""

        if from_edge_id not in connections:
            connections[from_edge_id] = {
                "dirs": {conn["dir"].lower()},
                "response": request.attrib["response"],
                "foes": request.attrib["foes"],
                "conns": 1
            }
        else:
            connections[from_edge_id]["dirs"].add(conn["dir"].lower())
            connections[from_edge_id]["response"] = combine_bitset(connections[from_edge_id]["response"],
                                                                   request.attrib["response"])
            connections[from_edge_id]["foes"] = combine_bitset(connections[from_edge_id]["foes"],
                                                               request.attrib["foes"])
            connections[from_edge_id]["conns"] += 1

        data_conns.append({
            "junctionId": junction.attrib["id"],
            "fromEdgeId": from_edge_id,
            "toEdgeId": toEdge.attrib["id"],
            "fromLaneId": fromLane.attrib["id"],
            "toLaneId": toLane.attrib["id"],
            "dir": conn["dir"],
            "connDistance": round(parse_ls(fromLane).distance(parse_ls(toLane)), 2)
        })

    data = []

    for edge in edges.values():
        junction = junctions[edge.attrib["to"]]

        conn = connections.get(edge.attrib["id"], {})

        # speed and length should be the same on all lanes
        lane = edge.find("lane", {"index": "0"})

        prio = int(edge.attrib["priority"])

        # determine priority relative to other edges
        prios = sorted(list(set(int(t.attrib["priority"]) for t in to_edges[edge.attrib["to"]])))

        ref = (len(prios) - 1) / 2
        cmp = prios.index(prio)
        if cmp > ref:
            prio = "higher"
        elif cmp < ref:
            prio = "lower"
        else:
            prio = "equal"

        dirs = "".join(sorted(conn.get("dirs", "")))

        # Remove uncommon speed values close together
        speed = float(lane.attrib["speed"])
        speed = max(8.33, speed)

        d = {
            "edgeId": edge.attrib["id"],
            "edgeType": edge.attrib["type"].replace("highway.", ""),
            "priority": prio,
            "speed": speed,
            "length": float(lane.attrib["length"]),
            "numLanes": len(edge.findall("lane")),
            "numConns": min(conn.get("conns", 0), 6),
            "numResponse": min(conn.get("response", "").count("1"), 3),
            "numFoes": min(conn.get("foes", "").count("1"), 3),
            "dir_l": "l" in dirs,
            "dir_r": "r" in dirs,
            "dir_s": "s" in dirs,
            "junctionType": junction.attrib["type"],
            "junctionSize": len(junction.findall("request"))
        }

        data.append(d)

    df = pd.DataFrame(data)
    return pd.get_dummies(df, columns=["priority"]), pd.DataFrame(data_conns)


def read_edges(folder):
    """ Combine resulting files for edges """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        df = pd.read_csv(os.path.join(folder, f))
        edge_id = df.iloc[0].edgeId

        aggr = df.groupby("laneId").agg(capacity=("flow", "max"))

        data.append({
            "edgeId": edge_id,
            "capacity": float(aggr.capacity.mean())
        })

    return pd.DataFrame(data)


def read_intersections(folder):
    """ Read intersection results """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        # there could be exclusive lanes and the capacity to two edges completely additive
        # however if the capacity is shared one direction could use way more than physical possible
        aggr = df.groupby("fromEdgeId").agg(capacity=("flow", "max")).reset_index()
        aggr.rename(columns={"fromEdgeId": "edgeId"})

        data.append(aggr)

    return pd.concat(data)


def read_routes(folder):
    """ Read routes from folder """
    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        data.append(df)

    df = pd.concat(data)
    aggr = df.groupby("edgeId").mean()

    return aggr.reset_index()


if __name__ == "__main__":
    parser = ArgumentParser(description="Util to convert data to csv")

    parser.add_argument("mode", nargs='?', help="Convert result file that create with one of the run scripts",
                        choices=["edges", "intersections", "routes"])
    parser.add_argument("--network", help="Path to sumo network")
    parser.add_argument("--input", help="Path to input file for conversion")

    args = parser.parse_args()

    if args.network:
        print("Extracting network features")
        edges, conns = read_network(args.network)

        edges.to_csv(args.network.replace(".xml", "-edges.csv.gz"), index=False)
        conns.to_csv(args.network.replace(".xml", "-conns.csv.gz"), index=False)

    df = None

    if args.input:

        if args.mode == "edges":
            df = read_edges(args.input)

        elif args.mode == "intersections":
            df = read_intersections(args.input)

        elif args.mode == "routes":
            df = read_routes(args.input)

        if df is not None:
            base = os.path.basename(args.input.rstrip("/"))
            df.to_csv(f"result_{args.mode}_{base}.csv", index=False)

    else:
        print("Skipping results, because --input is not given")
