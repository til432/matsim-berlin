package org.matsim.prepare.facilities;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.unimi.dsi.fastutil.objects.Object2DoubleMap;
import it.unimi.dsi.fastutil.objects.Object2DoubleOpenHashMap;
import org.apache.commons.math3.stat.descriptive.DescriptiveStatistics;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.geotools.api.feature.simple.SimpleFeature;
import org.locationtech.jts.geom.Envelope;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.TopologyException;
import org.matsim.api.core.v01.Coord;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.TransportMode;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.application.MATSimAppCommand;
import org.matsim.application.options.ShpOptions;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.network.algorithms.TransportModeNetworkFilter;
import org.matsim.core.utils.geometry.CoordUtils;
import org.matsim.core.utils.geometry.geotools.MGC;
import org.matsim.facilities.*;
import org.matsim.prepare.population.Attributes;
import org.matsim.run.OpenBerlinScenario;
import picocli.CommandLine;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

@CommandLine.Command(
	name = "facilities",
	description = "Creates MATSim facilities from shape-file and network"
)
public class CreateMATSimFacilities implements MATSimAppCommand {

	/**
	 * Filter link types that don't have a facility associated.
	 */
	public static final Set<String> IGNORED_LINK_TYPES = Set.of("motorway", "trunk",
		"motorway_link", "trunk_link", "secondary_link", "primary_link");
	private static final Logger log = LogManager.getLogger(CreateMATSimFacilities.class);
	@CommandLine.Option(names = "--network", required = true, description = "Path to car network")
	private Path network;

	@CommandLine.Option(names = "--output", required = true, description = "Path to output facility file")
	private Path output;

	@CommandLine.Option(names = "--facility-mapping", description = "Path to facility napping json", required = true)
	private Path mappingPath;

	@CommandLine.Option(names = "--zones-shp", description = "Path to shp file with zonal system", required = false)
	private Path zonesPath;

	@CommandLine.Mixin
	private ShpOptions shp;

	private MappingConfig config;

	public static void main(String[] args) {
		new CreateMATSimFacilities().execute(args);
	}

	/**
	 * Generate a new unique id within population.
	 */
	public static Id<ActivityFacility> generateId(ActivityFacilities facilities, SplittableRandom rnd) {

		Id<ActivityFacility> id;
		byte[] bytes = new byte[3];
		do {
			rnd.nextBytes(bytes);
			id = Id.create("f" + HexFormat.of().formatHex(bytes), ActivityFacility.class);

		} while (facilities.getFacilities().containsKey(id));

		return id;
	}

	private static double round(double f) {
		return BigDecimal.valueOf(f).setScale(4, RoundingMode.HALF_UP).doubleValue();
	}

	private static boolean hasAttribute(SimpleFeature ft, String name) {
		return ft.getAttribute(name) != null &&
			(Boolean.TRUE.equals(ft.getAttribute(name)) || "1".equals(ft.getAttribute(name)) ||
				(ft.getAttribute(name) instanceof Number number && number.intValue() > 0)
			);
	}

	@Override
	public Integer call() throws Exception {

		if (shp.getShapeFile() == null) {
			log.error("Shp file with facilities is required.");
			return 2;
		}

		config = new ObjectMapper().readerFor(MappingConfig.class).readValue(mappingPath.toFile());

		ShpOptions zoneShp = zonesPath != null ? new ShpOptions(zonesPath, "EPSG:25833", null) : null;
		ShpOptions.Index zones = zoneShp != null ? zoneShp.createIndex(OpenBerlinScenario.CRS, "SCHLUESSEL") : null;

		Network completeNetwork = NetworkUtils.readNetwork(this.network.toString());
		TransportModeNetworkFilter filter = new TransportModeNetworkFilter(completeNetwork);
		Network carOnlyNetwork = NetworkUtils.createNetwork();
		filter.filter(carOnlyNetwork, Set.of(TransportMode.car));

		List<SimpleFeature> fts = shp.readFeatures();

		List<Holder> data = fts.parallelStream()
			.map(ft -> processFeature(ft, carOnlyNetwork))
			.filter(Objects::nonNull)
			.toList();

		// Compute statistics on the attraction values
		DescriptiveStatistics work = new DescriptiveStatistics();
		DescriptiveStatistics other = new DescriptiveStatistics();

		for (Holder d : data) {
			work.addValue(d.attractionWork);
			other.addValue(d.attractionOther);
		}

		// Upper bounds for attraction
		double workUpper = work.getPercentile(99.99);
		double otherUpper = other.getPercentile(99.99);

		log.info("Work upper bound: {}", workUpper);
		log.info("Other upper bound: {}", otherUpper);

		ActivityFacilities facilities = FacilitiesUtils.createActivityFacilities();

		SplittableRandom rnd = new SplittableRandom();
		ActivityFacilitiesFactory f = facilities.getFactory();

		for (Holder h : data) {

			// Create mean coordinate
			OptionalDouble x = h.coords.stream().mapToDouble(Coord::getX).average();
			OptionalDouble y = h.coords.stream().mapToDouble(Coord::getY).average();

			if (x.isEmpty() || y.isEmpty()) {
				log.warn("Empty coordinate (Should never happen)");
				continue;
			}

			Id<ActivityFacility> id = generateId(facilities, rnd);

			ActivityFacility facility = f.createActivityFacility(id, CoordUtils.round(new Coord(x.getAsDouble(), y.getAsDouble())));
			for (String act : h.activities) {
				facility.addActivityOption(f.createActivityOption(act));
			}

			// Filter outliers from the attraction
			facility.getAttributes().putAttribute(Attributes.ATTRACTION_WORK,
				round(Math.min(Math.max(h.attractionWork, 5), workUpper))
			);
			facility.getAttributes().putAttribute(Attributes.ATTRACTION_OTHER,
				round(Math.min(Math.max(h.attractionOther, 5), otherUpper))
			);

			if (zones != null) {
				String zone = zones.query(facility.getCoord());
				if (zone != null) {
					facility.getAttributes().putAttribute(Attributes.LOR, Integer.parseInt(zone));
					facility.getAttributes().putAttribute(Attributes.ZONE, zone.substring(0, 2));
				}
			}

			facilities.addActivityFacility(facility);
		}

		log.info("Created {} facilities, writing to {}", facilities.getFacilities().size(), output);

		FacilitiesWriter writer = new FacilitiesWriter(facilities);
		writer.write(output.toString());

		return 0;
	}

	/**
	 * Sample points and choose link with the nearest points.
	 */
	private Holder processFeature(SimpleFeature ft, Network network) {

		Set<String> activities = activities(ft);
		if (activities.isEmpty())
			return null;

		// Pairs of coords and corresponding links
		List<Coord> coords = samplePoints((MultiPolygon) ft.getDefaultGeometry(), 23);
		List<Id<Link>> links = coords.stream().map(coord -> NetworkUtils.getNearestLinkExactly(network, coord).getId()).toList();

		Map<Id<Link>, Long> map = links.stream()
			.filter(l -> !IGNORED_LINK_TYPES.contains(NetworkUtils.getType(network.getLinks().get(l))))
			.collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));

		// Everything could be filtered and map empty
		if (map.isEmpty())
			return null;

		Object2DoubleMap<String> features = new Object2DoubleOpenHashMap<>();
		for (int i = 0; i < ft.getAttributeCount(); i++) {
			if (ft.getAttribute(i) instanceof Number number) {
				features.put(ft.getFeatureType().getDescriptor(i).getLocalName(), number.doubleValue());
			}
		}

		List<Map.Entry<Id<Link>, Long>> counts = map.entrySet().stream().sorted(Map.Entry.comparingByValue())
			.toList();

		// The "main" link of the facility
		Id<Link> link = counts.get(counts.size() - 1).getKey();

		Holder holder = new Holder(link, activities, new ArrayList<>(),
			FacilityAttractionModelWork.INSTANCE.predict(features, null),
			FacilityAttractionModelOther.INSTANCE.predict(features, null)
		);

		// Search for the original drawn coordinate of the associated link
		for (int i = 0; i < links.size(); i++) {
			if (links.get(i).equals(link)) {
				holder.coords.add(coords.get(i));
				break;
			}
		}

		return holder;
	}

	/**
	 * Sample coordinates within polygon.
	 */
	private List<Coord> samplePoints(MultiPolygon geometry, int n) {

		SplittableRandom rnd = new SplittableRandom();

		List<Coord> result = new ArrayList<>();
		Envelope bbox = geometry.getEnvelopeInternal();
		int max = n * 10;
		for (int i = 0; i < max && result.size() < n; i++) {

			Coord coord = CoordUtils.round(new Coord(
				bbox.getMinX() + (bbox.getMaxX() - bbox.getMinX()) * rnd.nextDouble(),
				bbox.getMinY() + (bbox.getMaxY() - bbox.getMinY()) * rnd.nextDouble()
			));

			try {
				if (geometry.contains(MGC.coord2Point(coord))) {
					result.add(coord);
				}
			} catch (TopologyException e) {
				if (geometry.getBoundary().contains(MGC.coord2Point(coord))) {
					result.add(coord);
				}
			}

		}

		if (result.isEmpty())
			result.add(MGC.point2Coord(geometry.getCentroid()));

		return result;
	}

	private Set<String> activities(SimpleFeature ft) {
		Set<String> act = new HashSet<>();

		for (Map.Entry<String, Set<String>> entries : config.values.entrySet()) {
			if (hasAttribute(ft, entries.getKey())) {
				act.addAll(entries.getValue());
			}
		}

		return act;
	}

	/**
	 * Temporary data holder for facilities.
	 */
	private record Holder(Id<Link> linkId, Set<String> activities, List<Coord> coords,
						  double attractionWork, double attractionOther) {
	}

	/**
	 * Helper class to define data structure for mapping.
	 */
	public static final class MappingConfig {

		private final Map<String, Set<String>> values = new HashMap<>();

		@JsonAnyGetter
		public Set<String> getActivities(String value) {
			return values.get(value);
		}

		@JsonAnySetter
		private void setActivities(String value, Set<String> activities) {
			values.put(value, activities);
		}

	}

}
