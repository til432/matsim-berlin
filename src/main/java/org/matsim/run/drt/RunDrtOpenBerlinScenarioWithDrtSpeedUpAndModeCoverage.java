/* *********************************************************************** *
 * project: org.matsim.*
 *                                                                         *
 * *********************************************************************** *
 *                                                                         *
 * copyright       : (C) 2017 by the members listed in the COPYING,        *
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

package org.matsim.run.drt;

import org.apache.log4j.Logger;
import org.matsim.analysis.linkpaxvolumes.LinkPaxVolumesAnalysisModule;
import org.matsim.analysis.personMoney.PersonMoneyEventsAnalysisModule;
import org.matsim.analysis.pt.stop2stop.PtStop2StopAnalysisModule;
import org.matsim.api.core.v01.Scenario;
import org.matsim.api.core.v01.population.Person;
import org.matsim.contrib.drt.run.DrtConfigGroup;
import org.matsim.contrib.drt.run.MultiModeDrtConfigGroup;
import org.matsim.contrib.drt.speedup.DrtSpeedUpParams;
import org.matsim.core.config.Config;
import org.matsim.core.config.ConfigUtils;
import org.matsim.core.controler.Controler;
import org.matsim.optDRT.MultiModeOptDrtConfigGroup;
import org.matsim.optDRT.OptDrt;
import org.matsim.run.RunBerlinScenario;
import org.matsim.run.dynamicShutdown.DynamicShutdownConfigGroup;
import org.matsim.run.dynamicShutdown.DynamicShutdownModule;

/**
* @author ikaddoura
*/

public class RunDrtOpenBerlinScenarioWithDrtSpeedUpAndModeCoverage {
	private static final Logger log = Logger.getLogger(RunDrtOpenBerlinScenarioWithDrtSpeedUpAndModeCoverage.class);

	public static void main(String[] args) {
		for (String arg : args) {
			log.info(arg);
		}

		if (args.length == 0) {
			args = new String[] { "scenarios/berlin-v5.5-1pct/input/drt/berlin-drt-v5.5-1pct.config.xml" };
		}

		Config config = RunDrtOpenBerlinScenario.prepareConfig(args, new MultiModeOptDrtConfigGroup(), new DynamicShutdownConfigGroup());
		for (DrtConfigGroup drtCfg : MultiModeDrtConfigGroup.get(config).getModalElements()) {
			if (drtCfg.getDrtSpeedUpParams().isEmpty()) {
				drtCfg.addParameterSet(new DrtSpeedUpParams());
			}
		}

		Scenario scenario = RunDrtOpenBerlinScenario.prepareScenario(config);
		for (Person person : scenario.getPopulation().getPersons().values()) {
			person.getPlans().removeIf((plan) -> plan != person.getSelectedPlan());
		}

		Controler controler = RunDrtOpenBerlinScenario.prepareControler(scenario);

		OptDrt.addAsOverridingModule(controler,
				ConfigUtils.addOrGetModule(scenario.getConfig(), MultiModeOptDrtConfigGroup.class));

		controler.addOverridingModule(new DynamicShutdownModule());
		controler.addOverridingModule(new LinkPaxVolumesAnalysisModule());
		controler.addOverridingModule(new PtStop2StopAnalysisModule());
		controler.addOverridingModule(new PersonMoneyEventsAnalysisModule());
		
		controler.run() ;
		
//		RunBerlinScenario.runAnalysis(controler);
	}

}

