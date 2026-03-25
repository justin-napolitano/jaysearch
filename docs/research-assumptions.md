# Research Assumptions and Design Inferences

## Purpose

This document separates source-backed claims from platform design inferences. It exists so the framework can remain intellectually honest: citations support some choices, but the platform also makes novel policy and architectural decisions that should not be disguised as if they were directly established by prior work.

## Categories

Use these categories for future design and implementation artifacts:

1. source-backed
   A claim is directly motivated by a cited paper, lecture, specification, or official documentation.
2. design-inference
   A claim extends, combines, or interprets cited sources into a platform-specific rule.
3. policy-choice
   A claim is a deliberate project choice, such as weights, thresholds, naming, or enforcement posture.
4. open-assumption
   A claim remains provisional and should be revisited during later design or implementation work.

## Current Assumptions Register

### Source-Backed

- mechanism design is a useful framing for choosing rules that shape behavior
- bounded rationality supports penalizing ambiguity and unsupported commitment
- provenance models justify explicit traceability requirements
- formal transition systems justify explicit move legality and state transitions
- inspection and review literature justify hostile review as a quality mechanism

### Design Inferences

- planning and implementation should be treated as two phases of one governed game
- the platform should be modeled as a nested game system rather than a single undifferentiated workflow
- the canonical graph should serve as the shared board across both phases
- `ExecPlan` should function as a commitment artifact rather than as the planning system
- project-manager systems should remain observer surfaces rather than authorities
- explicit contract import is preferable to implicit reverse-sync
- planning merge readiness and implementation merge readiness should be treated as distinct proof games
- remaining implementation work should be modeled as a canonical backlog graph rather than prose-only next steps
- safe parallel execution requires explicit conflict domains in addition to dependency edges
- a DeerFlow-inspired runtime should be layered above the existing kernel rather than replacing the kernel directly

### Policy Choices

- exact scoring weights in `spec/scoring.yaml`
- hard/direct planner stance by default
- specific CLI command names under `bin/planner`
- local-wins default for unresolved sync conflicts

### Open Assumptions

- exact readiness threshold for contract drafting
- exact scoring thresholds for planner and implementation phases
- exact reviewer/referee automation boundaries for future implementation tools
- exact runtime validator contract for the game graph itself
- exact runtime validator contract for the remaining-work graph
- exact memory model that preserves convenience without becoming hidden authority
- exact runtime artifact contract for sandbox outputs, session traces, and subagent results
- exact gateway surface that improves usability without bypassing local governance

## Usage Requirement

Future design and implementation documents should label major claims using these categories when the provenance would otherwise be ambiguous.

Deterministic enforcement should be recorded in `artifacts/planner/research/claim-registry.json` rather than inferred from prose alone.
