# Review Planner Control Plane Prompt

Use when:

- hostile-reviewing planner design artifacts before implementation
- checking that graph, session, and contract boundaries remain coherent
- checking that provider sync remains downstream and limited

Operating stance:

- assume the design is underspecified until proven otherwise
- identify contradictions between specs, prompts, and governance artifacts
- prioritize findings that would create hidden state, vague command semantics, or broken authority boundaries

Required outputs:

- ordered findings with severity and file references
- explicit assumptions or open questions
- short summary of residual risk if no blocking issue is found
