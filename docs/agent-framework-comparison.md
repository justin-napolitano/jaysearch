# Agent Framework Comparison

## Purpose

This document compares the most relevant current agent/runtime frameworks against the needs of this repository. It is not a generic leaderboard. The point is to evaluate which frameworks fit a governed kernel with explicit local state, merge-gated execution, and human authority boundaries.

## Scope

Frameworks compared here:

- Microsoft Agent Framework
- LangGraph
- OpenAI Agents SDK
- CrewAI
- DeerFlow as a product-pattern reference rather than a pure framework

Primary source links:

- Microsoft Agent Framework overview: `https://learn.microsoft.com/en-us/agent-framework/overview/`
- Microsoft Agent Framework FAQ: `https://learn.microsoft.com/en-us/agent-framework/support/faq`
- Microsoft Agent Framework GitHub: `https://github.com/microsoft/agent-framework`
- LangGraph docs: `https://docs.langchain.com/oss/javascript/langgraph`
- OpenAI Agents SDK docs: `https://platform.openai.com/docs/guides/agents-sdk/`
- OpenAI Agents SDK Python docs: `https://openai.github.io/openai-agents-python/`
- CrewAI docs: `https://docs.crewai.com/`
- DeerFlow GitHub: `https://github.com/bytedance/deer-flow`

## Repo Lens

This repository already has a strong kernel:

- canonical local artifacts
- graph-backed work state
- deterministic validation
- explicit human finalization
- explicit prohibition on hidden authority

What it does not yet have is a strong runtime harness:

- skill and tool loading
- session runtime and handoffs
- memory model
- sandbox abstraction
- service ingress and UI surfaces

Any framework choice should therefore be judged as a possible harness layer, not as a replacement for the kernel.

## Short Verdict

### Microsoft Agent Framework

Best fit if the organization wants Microsoft alignment, enterprise workflow primitives, .NET and Python support, middleware, telemetry, and a forward path from AutoGen and Semantic Kernel.

### LangGraph

Best fit if low-level orchestration control and explicit workflow/state graphs matter more than enterprise ecosystem alignment.

### OpenAI Agents SDK

Best fit if the team wants the smallest useful primitive set and is willing to build more of the runtime shape itself.

### CrewAI

Best fit if the team wants a more packaged multi-agent workflow product quickly, but it is less attractive as the substrate for this repo’s explicit-governance model.

### DeerFlow

Best thought of as a runtime product reference and feature benchmark, not as the most obvious underlying framework choice for this repository.

## Compare by Dimension

### 1. Kernel Compatibility

Microsoft Agent Framework:

- compatible as a harness layer
- does not inherently replace the repo’s graph or ExecPlan authority
- heavy enough that governance boundaries would need to be defended explicitly

LangGraph:

- highly compatible with the repo’s explicit state-machine mindset
- feels natural beside graph-backed canonical state
- does not force a product-shaped runtime model too early

OpenAI Agents SDK:

- compatible because it is minimal
- easier to keep subordinate to the repo’s kernel
- would require more custom runtime assembly for sessions, memory, and service layers

CrewAI:

- more likely to push the repo toward its own team/task abstractions
- workable, but less naturally aligned with the local graph and governed artifact model

DeerFlow:

- inspirationally compatible at the harness level
- not itself the kernel answer for this repository

### 2. Enterprise and Microsoft Fit

Microsoft Agent Framework is strongest here.

Good:

- Microsoft-backed
- open source
- Python and .NET
- Azure-friendly without being Azure-only
- explicit successor path from older Microsoft agent stacks

Risk:

- preview maturity means interface churn is still possible

LangGraph and OpenAI Agents SDK are both credible enterprise choices, but neither gives the same Microsoft-house alignment story.

### 3. Orchestration Model

LangGraph is strongest on explicit orchestration.

Microsoft Agent Framework appears strong on workflows, sessions, middleware, and runtime services, which is attractive if the repo grows into a broader internal platform.

OpenAI Agents SDK intentionally keeps orchestration smaller and cleaner. That is a strength if the team wants fewer abstractions and a weakness if the team wants more built-in runtime scaffolding.

CrewAI is more opinionated around agent-team execution patterns than around explicit state-machine governance.

### 4. Memory and Hidden-State Risk

For this repository, this dimension matters more than benchmarks or demos.

Best posture:

- memory should help agents work
- memory must not become canonical authority
- durable decisions must reconcile into local artifacts

OpenAI Agents SDK and LangGraph are easier to keep honest here because they do less for you implicitly.

Microsoft Agent Framework can still fit, but the repo must explicitly constrain session and memory behavior so it does not drift into hidden-state authority.

DeerFlow-style product ergonomics are attractive, but they are also where hidden-state risk grows fastest.

### 5. Tooling, Integrations, and Runtime Surface

Microsoft Agent Framework looks strongest if you want a broader enterprise runtime surface.

OpenAI Agents SDK is strongest if you want a smaller tool/handoff/guardrail core.

LangGraph is strong if you want to build the runtime shape deliberately instead of inheriting one.

CrewAI gives more out-of-the-box multi-agent workflow packaging but less confidence as the long-term governed substrate here.

### 6. Governance Friendliness

Best fit for this repo’s governance posture:

1. LangGraph
2. OpenAI Agents SDK
3. Microsoft Agent Framework
4. DeerFlow as reference pattern
5. CrewAI

Best fit for this organization if Microsoft alignment matters materially:

1. Microsoft Agent Framework
2. LangGraph
3. OpenAI Agents SDK
4. DeerFlow as reference pattern
5. CrewAI

Those rankings differ for a reason. The best technical fit for the current kernel is not automatically the best organizational fit.

## Microsoft Agent Framework: Specific Read

What looks good:

- open source and Microsoft-backed
- likely durable inside a Microsoft-heavy environment
- enterprise posture: middleware, telemetry, workflows, sessions
- reasonable candidate for the runtime/harness layer

What does not solve by itself:

- canonical local graph authority
- ExecPlan-first workflow
- governed merge-readiness
- explicit reconciliation from runtime actions into durable local artifacts

What could go wrong:

- the team assumes Microsoft alignment means the framework should become the new source of truth
- session state and runtime middleware become de facto authority instead of convenience layers
- the repo weakens its current invariants in order to “fit the framework”

## Recommended Posture for This Repo

### If Microsoft Alignment Wins

Use Microsoft Agent Framework as the harness/runtime candidate and keep this repository’s graph, ExecPlan, and merge-governance surfaces as the kernel.

That means:

- do not move canonical authority into framework runtime state
- do not let service ingress bypass local artifact reconciliation
- use framework workflows and sessions as execution machinery, not truth

### If Kernel Purity Wins

Favor LangGraph or OpenAI Agents SDK because they make it easier to keep the runtime subordinate to the kernel.

### If Product Ergonomics Win

Borrow DeerFlow ideas for the harness surface, but still pick a more defensible underlying runtime substrate for this repository.

## Practical Recommendation

Current recommendation:

1. Continue researching Microsoft Agent Framework as the leading organizational-fit candidate.
2. Keep LangGraph as the strongest technical comparison point.
3. Keep OpenAI Agents SDK as the small-primitive fallback.
4. Keep DeerFlow as a feature and UX benchmark.
5. Do not commit to CrewAI for this repository unless speed-to-demo outweighs governance fidelity.

## Open Questions

1. Does Microsoft Agent Framework provide enough control over runtime state and checkpointing to keep local artifacts canonical?
2. How much of its session model is helpful versus risky for this repo’s no-hidden-authority stance?
3. Does the organization value .NET parity enough to outweigh a potentially cleaner Python-first stack?
4. Would a hybrid approach work better: Microsoft Agent Framework for gateway/runtime, local kernel for authority, and explicit reconciliation contracts between them?
