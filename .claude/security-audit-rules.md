# Project security audit exclusions

Read by the `security-auditor` subagent. Each line is a finding class this project has already
decided is not a defect here, with the reason. Add a rule only after an audit produced that
finding and the team judged it noise.

Keep every rule narrow enough that it could not hide a real defect. "Ignore findings in the API
layer" is too broad. "Ignore missing authentication on `/healthz`, which is intentionally public"
is a rule.

- (none yet)
