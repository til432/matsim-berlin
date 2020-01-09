/* *********************************************************************** *
 * project: org.matsim.*
 * ReRoute.java
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 * copyright       : (C) 2008 by the members listed in the COPYING,        *
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

import javax.inject.Provider;

import org.matsim.api.core.v01.Scenario;
import org.matsim.core.config.groups.ChangeModeConfigGroup;
import org.matsim.core.config.groups.GlobalConfigGroup;
import org.matsim.core.controler.Controler;
import org.matsim.core.gbl.MatsimRandom;
import org.matsim.core.population.algorithms.PlanAlgorithm;
import org.matsim.core.replanning.modules.AbstractMultithreadedModule;
import org.matsim.core.router.TripRouter;
import org.matsim.facilities.ActivityFacilities;

/**
 * Uses the routing algorithm provided by the {@linkplain Controler} for 
 * calculating the routes of plans during Replanning.
 *
 * @author mrieser
 */
public class ChangeSingleTripModeAndSingleTripReRouteModule extends AbstractMultithreadedModule {
	
	private ActivityFacilities facilities;

	private final Provider<TripRouter> tripRouterProvider;
	private final ChangeModeConfigGroup changeModeConfigGroup;

	public ChangeSingleTripModeAndSingleTripReRouteModule(ActivityFacilities facilities, Provider<TripRouter> tripRouterProvider, GlobalConfigGroup globalConfigGroup, ChangeModeConfigGroup changeModeConfigGroup) {
		super(globalConfigGroup);
		this.facilities = facilities;
		this.tripRouterProvider = tripRouterProvider;
		this.changeModeConfigGroup = changeModeConfigGroup;
	}

	@Override
	public final PlanAlgorithm getPlanAlgoInstance() {
			return new ChangeSingleTripModeAndSingleTripReRoutePlanRouter(
					tripRouterProvider.get(),
					facilities,
					MatsimRandom.getLocalInstance(),
					changeModeConfigGroup
					);
	}

}
