package org.matsim.prepare.choices;

import org.matsim.api.core.v01.population.Plan;
import org.matsim.core.population.PersonUtils;
import org.matsim.modechoice.PlanCandidate;
import org.matsim.modechoice.PlanModel;
import org.matsim.modechoice.search.TopKChoicesGenerator;

import java.util.*;

/**
 * Generator to create candidates with different modes.
 */
public class DiversePlanGenerator implements ChoiceGenerator {

	private final int topK;
	private final TopKChoicesGenerator gen;
	private final SplittableRandom rnd = new SplittableRandom(0);

	DiversePlanGenerator(int topK, TopKChoicesGenerator generator) {
		this.topK = topK;
		this.gen = generator;
	}

	@Override
	public List<PlanCandidate> generate(Plan plan, PlanModel planModel, Set<String> consideredModes) {

		List<String[]> chosen = new ArrayList<>();
		chosen.add(planModel.getCurrentModes());

		// Chosen candidate from data
		PlanCandidate existing = gen.generatePredefined(planModel, chosen).get(0);

		List<PlanCandidate> candidates = new ArrayList<>();
		boolean carUser = PersonUtils.canUseCar(planModel.getPerson());
		Set<String> modes = new HashSet<>(consideredModes);

		for (String mode : modes) {
			if (!carUser && mode.equals("car"))
				continue;

			List<PlanCandidate> tmp = gen.generate(planModel, Set.of(mode), null);
			if (!tmp.isEmpty())
				candidates.add(tmp.get(0));
		}

		candidates.addFirst(existing);

		// Add combination of modes as well
		addToCandidates(candidates, gen.generate(planModel, modes, null), carUser ? "car" : "ride", 1);
		addToCandidates(candidates, gen.generate(planModel, consideredModes, null), null, 1);

		// Remove the primary mode to generate remaining alternatives
		modes.remove(carUser ? "car" : "ride");
		addToCandidates(candidates, gen.generate(planModel, modes, null), null, 2);

		return candidates.stream().distinct().limit(this.topK).toList();
	}

	private void addToCandidates(List<PlanCandidate> candidates, List<PlanCandidate> topK, String requireMode, int n) {

		topK.removeIf(candidates::contains);

		if (requireMode != null) {
			topK.removeIf(c -> !c.containsMode(requireMode));
		}

		for (int i = 0; i < n; i++) {
			if (topK.size() > 1)
				candidates.add(topK.remove(rnd.nextInt(topK.size())));
		}
	}

}
