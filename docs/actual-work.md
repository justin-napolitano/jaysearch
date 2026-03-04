Create branch

git checkout -b draft-execplan/platform-validator-jay-$(date +%Y%m%d)

Create the ExecPlan file

touch .agent/execplans/$(date +%Y%m%d)-platform-validator-jay-execplan.md

Open the file

nano .agent/execplans/$(date +%Y%m%d)-platform-validator-jay-execplan.md

Paste the plan contents.

Save the file.

Stage the plan

git add .agent/execplans/*platform-validator*

Commit the draft

git commit

Commit message

chore(execplan): draft platform validator implementation

Introduce ExecPlan for building validation engine and local CI tools.

Metadata:
  ExecPlan: platform-validator-YYYYMMDD

Run Codex against the plan
