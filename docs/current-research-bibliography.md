# Current Research Bibliography

This bibliography captures the sources currently used to justify the research, design-review, candidate-evaluation, and recommendation loop.

It complements:

- `docs/references.md`
- `artifacts/planner/research/bibliography-graph.json`
- `docs/research-assumptions.md`

## Agent Feedback And Critique

1. Madaan et al. `Self-Refine: Iterative Refinement with Self-Feedback`.
   Link: https://arxiv.org/abs/2303.17651

   Current use:

   - supports explicit iterative feedback loops
   - informs design iteration and candidate refinement
   - does not by itself justify trusting unsupported self-critique

2. Shinn et al. `Reflexion: Language Agents with Verbal Reinforcement Learning`.
   Link: https://arxiv.org/abs/2303.11366

   Current use:

   - supports feedback plus retained context for agent improvement
   - informs memory-aware review and iteration loops
   - does not replace external validation or governance gates

3. Gou et al. `CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing`.
   Link: https://arxiv.org/abs/2305.11738

   Current use:

   - supports tool-grounded critique over unsupported introspection
   - informs design-review automation and evidence-backed review
   - motivates routing critique through local artifacts, source packets, validators, and tests

## Task-Grounded Software Evaluation

4. Jimenez et al. `SWE-bench: Can Language Models Resolve Real-World GitHub Issues?`.
   Link: https://arxiv.org/abs/2310.06770

   Current use:

   - supports task-grounded software evaluation rather than plausibility-only scoring
   - informs `research_evaluation_packet` and `research_recommendation_packet`
   - motivates requiring candidates to cite evaluation records before recommendation

5. Google DeepMind. `AlphaEvolve: A coding agent for scientific and algorithmic discovery`.
   Link: https://arxiv.org/abs/2506.13131

   Current use:

   - supports an evolutionary generate/evaluate/select loop for code candidates
   - motivates keeping implementation attempts separate from selected solution artifacts
   - does not by itself solve project decomposition, governance, or provenance requirements

## ERA And Computational Discovery

6. Google Research. `Empirical Research Assistance (ERA): From Nature publication to catalyzing Computational Discovery`.
   Link: https://research.google/blog/empirical-research-assistance-era-from-nature-publication-to-catalyzing-computational-discovery/

   Current use:

   - supports the design relevance of an empirical coding loop that searches literature, writes code, explores solutions, combines techniques, and evaluates results
   - informs Jaysearch's explicit separation between research intake, candidate generation, evaluation, and selected solution artifacts
   - does not imply Jaysearch has equivalent scientific benchmark performance or Gemini-backed capabilities

7. Aygun et al. `An AI system to help scientists write expert-level empirical software`.
   Link: https://www.nature.com/articles/s41586-026-10658-6

   Current use:

   - supports the ERA framing of expert-level empirical software generation driven by a quality metric
   - informs the generate/evaluate/select pattern and the value of tree-search-like exploration over candidate implementations
   - motivates explicit evidence and metric capture for implementation attempts

8. Google Research. `ERA code and experiments`.
   Link: https://github.com/google-research/era/tree/main/era_applications

   Current use:

   - provides a concrete public artifact surface for ERA applications and experiments
   - motivates keeping code, experiments, manuscripts, and evaluation evidence linkable from the bibliography
   - supports Jaysearch's preference for source-backed artifact references over prose-only claims

## Platform Governance Foundations

9. Nash. `Equilibrium Points in N-Person Games`.
   Link: https://pubmed.ncbi.nlm.nih.gov/16588946/

   Current use:

   - informs the platform's game framing
   - does not determine platform payoffs or scoring weights directly

10. Maskin. `Mechanism Design: How to Implement Social Goals`.
   Link: https://www.nobelprize.org/prizes/economic-sciences/2007/maskin/lecture/

   Current use:

   - supports explicit rule and incentive design
   - informs anti-cheat and governance framing

11. Myerson. `Perspectives on Mechanism Design in Economic Theory`.
   Link: https://www.nobelprize.org/prizes/economic-sciences/2007/myerson/lecture/

   Current use:

   - supports mechanism-design framing
   - informs separation between desired outcomes, rules, and allowed moves

12. Simon. `A Behavioral Model of Rational Choice`.
   Link: https://academic.oup.com/qje/article/69/1/99/1919737

   Current use:

   - supports bounded-rationality assumptions
   - informs bounded search budgets and explicit stopping rules

## Provenance, State, And Inspection

13. W3C. `PROV-Overview`.
   Link: https://www.w3.org/TR/2013/NOTE-prov-overview-20130430/

   Current use:

   - supports provenance-first packet and artifact references
   - informs traceable DAG and handoff contracts

14. W3C. `PROV-DM: The PROV Data Model`.
    Link: https://dvcs.w3.org/hg/prov/raw-file/default/model/prov-dm.html

    Current use:

    - supports structured provenance modeling
    - informs source refs, artifact refs, and graph relationships

15. Harel. `Statecharts: a visual formalism for complex systems`.
    Link: https://www.sciencedirect.com/science/article/pii/0167642387900359

    Current use:

    - supports explicit state and transition modeling
    - informs governance transition legality and orchestration state

16. Fagan. `Advances in Software Inspections`.
    Link: https://research.ibm.com/publications/advances-in-software-inspections

    Current use:

    - supports structured inspection and review discipline
    - informs critical review gates

17. Myers. `A Controlled Experiment in Program Testing and Code Walkthroughs/Inspections`.
    Link: https://research.ibm.com/publications/a-controlled-experiment-in-program-testing-and-code-walkthroughsinspections

    Current use:

    - supports inspection/testing distinction
    - informs keeping review, validation, and execution evidence separate

## Source Discipline

The bibliography supports design choices but does not make the platform's exact scoring weights, DAG boundaries, or tool contracts mathematically inevitable.

Those are platform design decisions and should remain labeled as design inferences when they extend beyond the cited sources.
