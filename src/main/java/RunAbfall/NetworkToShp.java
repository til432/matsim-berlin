package RunAbfall;

import java.util.ArrayList;
import java.util.Collection;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.network.Link;
import org.matsim.api.core.v01.network.Network;
import org.matsim.api.core.v01.network.Node;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.network.NetworkUtils;
import org.matsim.core.scenario.ScenarioUtils;
import org.matsim.core.utils.geometry.CoordinateTransformation;
import org.matsim.core.utils.geometry.geotools.MGC;
import org.matsim.core.utils.geometry.transformations.TransformationFactory;
import org.matsim.core.utils.gis.PointFeatureFactory;
import org.matsim.core.utils.gis.PolylineFeatureFactory;
import org.matsim.core.utils.gis.ShapeFileWriter;
import org.opengis.feature.simple.SimpleFeature;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import com.vividsolutions.jts.geom.Coordinate;

public class NetworkToShp {

	public static void main(String[] args) {
		Config config = ConfigUtils.createConfig();
	    config.network().setInputFile("original-input-data/berlin-v5.2-1pct.output_network.xml.gz");
	    config.global().setCoordinateSystem(TransformationFactory.GK4);
	    Scenario scenario = ScenarioUtils.loadScenario(config);
	    Network network = scenario.getNetwork();
	         
	    CoordinateReferenceSystem crs = MGC.getCRS("EPSG:4326");    // EPSG Code for Swiss CH1903_LV03/+LV95 coordinate system


	            Collection<SimpleFeature> features = new ArrayList<>();
	            PolylineFeatureFactory linkFactory = new PolylineFeatureFactory.Builder().
	                    setCrs(crs).
	                    setName("link").
	                    addAttribute("ID", String.class).
	                    addAttribute("fromID", String.class).
	                    addAttribute("toID", String.class).
	                    addAttribute("length", Double.class).
	                    addAttribute("type", String.class).
	                    addAttribute("capacity", Double.class).
	                    addAttribute("freespeed", Double.class).
	                    create();


	            for (Link link : network.getLinks().values()) {
	                Coordinate fromNodeCoordinate = new Coordinate(link.getFromNode().getCoord().getX(), link.getFromNode().getCoord().getY());
	                Coordinate toNodeCoordinate = new Coordinate(link.getToNode().getCoord().getX(), link.getToNode().getCoord().getY());
	                Coordinate linkCoordinate = new Coordinate(link.getCoord().getX(), link.getCoord().getY());
	                SimpleFeature ft = linkFactory.createPolyline(new Coordinate [] {fromNodeCoordinate, linkCoordinate, toNodeCoordinate},
	                        new Object [] {link.getId().toString(), link.getFromNode().getId().toString(),link.getToNode().getId().toString(), link.getLength(), NetworkUtils.getType(link), link.getCapacity(), link.getFreespeed()}, null);
	                features.add(ft);
	            }
	            		
	            ShapeFileWriter.writeGeometries(features, "C:/Users/ericar/OneDrive/Dokumente/Studium/0 Masterarbeit/network_links.shp");


	            features = new ArrayList<>();
	            PointFeatureFactory nodeFactory = new PointFeatureFactory.Builder().
	                    setCrs(crs).
	                    setName("nodes").
	                    addAttribute("ID", String.class).
	                    create();


	            for (Node node : network.getNodes().values()) {
	                SimpleFeature ft = nodeFactory.createPoint(node.getCoord(), new Object[] {node.getId().toString()}, null);
	                features.add(ft);
	            }
	            ShapeFileWriter.writeGeometries(features, "C:/Users/ericar/OneDrive/Dokumente/Studium/0 Masterarbeit/network_nodes.shp");


	
	}
}
