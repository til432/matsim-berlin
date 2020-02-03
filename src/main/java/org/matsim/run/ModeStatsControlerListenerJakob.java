/* *********************************************************************** *
 * project: org.matsim.*
 * ScoreStats.java
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 * copyright       : (C) 2007 by the members listed in the COPYING,        *
 *                   LICENSE and WARRANTY file.                            *
 * email           : info at matsim dot org                                *
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *   See also COPYING, LICENSE and WARRANTY file                           *
 *                                                                         *
 * *********************************************************************** */

package org.matsim.run;

import org.apache.log4j.Logger;
import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.population.Person;
import org.matsim.api.core.v01.population.Plan;
import org.matsim.api.core.v01.population.Population;
import org.matsim.core.config.groups.ControlerConfigGroup;
import org.matsim.core.config.groups.PlanCalcScoreConfigGroup;
import org.matsim.core.controler.OutputDirectoryHierarchy;
import org.matsim.core.controler.events.IterationEndsEvent;
import org.matsim.core.controler.events.ShutdownEvent;
import org.matsim.core.controler.events.StartupEvent;
import org.matsim.core.controler.listener.IterationEndsListener;
import org.matsim.core.controler.listener.ShutdownListener;
import org.matsim.core.controler.listener.StartupListener;
import org.matsim.core.router.AnalysisMainModeIdentifier;
import org.matsim.core.router.MainModeIdentifier;
import org.matsim.core.router.TripStructureUtils;
import org.matsim.core.router.TripStructureUtils.Trip;
import org.matsim.core.utils.charts.XYLineChart;
import org.matsim.core.utils.io.IOUtils;
import org.matsim.core.utils.io.UncheckedIOException;

import javax.inject.Inject;
import java.io.BufferedWriter;
import java.io.IOException;
import java.util.*;
import java.util.Map.Entry;

/**
 * Calculates at the end of each iteration mode statistics, based on the main mode identifier of a trip chain.
 * For multi-modal trips, this is only as accurate as your main mode identifier.
 * The calculated values are written to a file, each iteration on
 * a separate line.
 *
 * @author mrieser
 *
 * TODO:
 */
public class ModeStatsControlerListenerJakob implements StartupListener, IterationEndsListener,
        ShutdownListener {

	public static final String FILENAME_MODESTATS = "modestats";

	final private Population population;
	
	final private BufferedWriter modeOut ;
	final private String modeFileName ;

	private final boolean createPNG;
	private final ControlerConfigGroup controlerConfigGroup;

	Map<String, Map<Integer, Double>> modeHistories = new HashMap<>() ;
	private int minIteration = 0;
	private MainModeIdentifier mainModeIdentifier;
	private Map<String, Double> modeCnt = new TreeMap<>() ;
	
	private final Set<String> modes;

	private final static Logger log = Logger.getLogger(org.matsim.analysis.ModeStatsControlerListener.class);


	//jr
//	private Map<Id<Person>, Map<Integer, Set<String>>> megaMap = new LinkedHashMap<>(); //old
		private Map<Id<Person>, Map<Integer, Set<String>>> megaMap = new LinkedHashMap<>();
	private Map<String, Double> cumulativeModeCnt = new TreeMap<>() ;

	@Inject
    ModeStatsControlerListenerJakob(ControlerConfigGroup controlerConfigGroup, Population population1, OutputDirectoryHierarchy controlerIO,
                                    PlanCalcScoreConfigGroup scoreConfig, AnalysisMainModeIdentifier mainModeIdentifier) {

		this.controlerConfigGroup = controlerConfigGroup;
		this.population = population1;
		this.modeFileName = controlerIO.getOutputFilename(FILENAME_MODESTATS);
//		this.createPNG = controlerConfigGroup.isCreateGraphs();
		this.createPNG = true ; //jr
		this.modeOut = IOUtils.getBufferedWriter(this.modeFileName+ "JAKOBXXXX" + ".txt"); //jr
		try {
			this.modeOut.write("Iteration");
			this.modes = new TreeSet<>();
			this.modes.addAll(scoreConfig.getAllModes());
			for (String mode : modes) {
				this.modeOut.write("\t" + mode);
			}
			this.modeOut.write("\n");
			;
		} catch (IOException e) {
			throw new UncheckedIOException(e);
		}
		this.mainModeIdentifier = mainModeIdentifier;
	}

	@Override
	public void notifyStartup(final StartupEvent event) {
		this.minIteration = controlerConfigGroup.getFirstIteration();
	}

	@Override
	public void notifyIterationEnds(final IterationEndsEvent event) {
		collectModeShareInfo(event) ;
	}

	private void collectModeShareInfo(final IterationEndsEvent event) {
		for (Person person : this.population.getPersons().values()) {

			//jr
			Map<Integer, Set<String>> mapForPerson = megaMap.get(person.getId()); // open map for person
			if (mapForPerson == null) {
				mapForPerson = new LinkedHashMap<>();
			}

			Plan plan = person.getSelectedPlan() ;
			List<Trip> trips = TripStructureUtils.getTrips(plan) ;
			Integer tripNumber = 0 ;
			for ( Trip trip : trips ) {



				String mode = this.mainModeIdentifier.identifyMainMode( trip.getTripElements() ) ;
				// yy as stated elsewhere, the "computer science" mode identification may not be the same as the "transport planning" 
				// mode identification.  Maybe revise.  kai, nov'16

				// jr:
				tripNumber++ ;
				Set<String> setForPersonTrip = mapForPerson.get(tripNumber); // open set for person trip
				if (setForPersonTrip == null) {
					setForPersonTrip = new HashSet<>();
				}
				setForPersonTrip.add(mode);
				mapForPerson.put(tripNumber, setForPersonTrip); // close set for person trip
				// modeCnt seems superfluous, now that we have more detailed information!

				Double cnt = this.modeCnt.get( mode );
				if ( cnt==null ) {
					cnt = 0. ;
				}
				this.modeCnt.put( mode, cnt + 1 ) ;
			}

			megaMap.put(person.getId(), mapForPerson); // reinsert map for person
		}


		// jr
		int totalPersonTripCount = 0;
		{

			for (Map<Integer,Set<String>> mapForPerson : megaMap.values()) {
				for (Set<String> setForPersonTrip : mapForPerson.values()) {
					totalPersonTripCount++;
					for (String mode : setForPersonTrip) {
						Double cnt = this.cumulativeModeCnt.get( mode );
						if ( cnt==null ) {
							cnt = 0. ;
						}
						this.cumulativeModeCnt.put( mode, cnt + 1 ) ;
					}
				}
			}
		}




		double sum = 0 ;
		for ( Double val : this.modeCnt.values() ) {
			sum += val ;
		}

		// JR JR JR
		sum = totalPersonTripCount ;
		modeCnt = cumulativeModeCnt ;
		
		try {
			this.modeOut.write( String.valueOf(event.getIteration()) ) ;
			log.info("Mode shares over all " + sum + " trips found. MainModeIdentifier: " + mainModeIdentifier.getClass());
			for ( String mode : modes ) {
				Double cnt = this.modeCnt.get(mode) ;
				double share = 0. ;
				if ( cnt!=null ) {
					share = cnt/sum;
				}
				log.info("-- mode share of mode " + mode + " = " + share );
				this.modeOut.write( "\t" + share ) ;
				
				Map<Integer, Double> modeHistory = this.modeHistories.get(mode) ;
				if ( modeHistory == null ) {
					modeHistory = new TreeMap<>() ;
					this.modeHistories.put(mode, modeHistory) ;
				}
				modeHistory.put( event.getIteration(), share ) ;
				
			}
			this.modeOut.write("\n");
			this.modeOut.flush();
		} catch (IOException e) {
			e.printStackTrace();
		}


		// yyyy the following does not work!!
		// Why? The charts seem to be useful (JB, April 2017)
		if (this.createPNG && event.getIteration() > this.minIteration) {
			// create chart when data of more than one iteration is available.
			XYLineChart chart = new XYLineChart("Mode Choice Coverage Statistics", "iteration", "mode choice coverage (%)");
			for ( Entry<String, Map<Integer, Double>> entry : this.modeHistories.entrySet() ) {
				String mode = entry.getKey() ;
				Map<Integer, Double> history = entry.getValue() ;
//				log.warn( "about to add the following series:" ) ;
//				for ( Entry<Integer, Double> item : history.entrySet() ) {
//					log.warn( item.getKey() + " -- " + item.getValue() );
//				}
				chart.addSeries(mode, history ) ;
			}
			chart.addMatsimLogo();
			chart.saveAsPng(this.modeFileName + "JAKOBXXXXXXXX" + ".png", 800, 600);
		}
		modeCnt.clear();
	}

	@Override
	public void notifyShutdown(final ShutdownEvent controlerShudownEvent) {
		try {
			this.modeOut.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

	}
}
