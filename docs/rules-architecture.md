# Rules Architecture

This repository separates rules into three layers:

1. `spec/` machine-checkable canonical contracts
2. `policy/` concise normative governance text
3. `docs/` explanatory and onboarding material

If a rule is enforced by code, it must be defined in `spec/`.
