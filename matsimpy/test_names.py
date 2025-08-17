import pandas as pd

all_stations = []

lines = ["s2", "s8", "s75"]
for line in lines:
    times = pd.read_csv(f"lines/{line}_times.csv", sep=";", encoding="cp1252", header=0)
    all_stations = all_stations + list(times["from"].values)
    all_stations = all_stations + list(times["to"].values)


for line in lines:
    stations = pd.read_csv(f"lines/{line}_line.csv", sep=";", encoding="cp1252", header=None)
    all_stations = all_stations + list(stations[0].values)

freq = pd.read_csv("lines/frequency.csv", sep=";", encoding="cp1252", header=0)
all_stations = all_stations + list(freq["from"].values)
all_stations = all_stations + list(freq["to"].values)

unique_stations = sorted(set(all_stations))

# Create DataFrame with second column empty
df = pd.DataFrame({
    "name": unique_stations,
    "forward": [f"{name}_forward_link_placeholder" for name in unique_stations],
    "backward": [f"{name}_backward_link_placeholder" for name in unique_stations]
})

# Save to CSV with semicolon separator
df.to_csv("stations_links.csv", sep=";", index=False)

