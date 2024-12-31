#!/usr/bin/env bash

CONFIG="./input/v6.4/berlin-v6.4.config.xml"
JVM_ARGS="-Xmx22G -Xms22G -XX:+AlwaysPreTouch -XX:+UseParallelGC"

run_plan() {
    echo "Running plan choices with $1"
    java $JVM_ARGS -cp matsim-berlin-*.jar org.matsim.prepare.choices.ComputePlanChoices --config $CONFIG\
      --scenario org.matsim.run.OpenBerlinScenario\
      --args --10pct\
      --modes walk,pt,car,bike,ride\
      $1
}

run_trip() {
    echo "Running trip choices with $1"
    java $JVM_ARGS -cp matsim-berlin-*.jar org.matsim.prepare.choices.ComputeTripChoices --config $CONFIG\
      --scenario org.matsim.run.OpenBerlinScenario\
      --args --10pct\
      --modes walk,pt,car,bike,ride\
      $1
}

#run_eval "--plan-candidates bestK --top-k 3"
#run_eval "--plan-candidates bestK --top-k 5"
#run_eval "--plan-candidates bestK --top-k 9"
#run_eval "--plan-candidates bestK --top-k 3 --time-util-only"
#run_eval "--plan-candidates bestK --top-k 5 --time-util-only"
#run_eval "--plan-candidates bestK --top-k 9 --time-util-only"
#run_eval "--plan-candidates random --top-k 3"
#run_eval "--plan-candidates random --top-k 5"
#run_eval "--plan-candidates random --top-k 9"
#run_eval "--plan-candidates diverse --top-k 9"
#run_eval "--plan-candidates diverse --top-k 9 --time-util-only"

run_trip ""

run_plan "--plan-candidates subtour --top-k 70"