---
source: internal_ir_process_sample
collection: defense
sensitivity: internal
---
# Incident response process sample

Use the four-stage incident handling loop: preparation, detection and analysis, containment eradication and recovery, and post-incident improvement.

Key internal response checkpoints:
1. Confirm alert source, affected business service, asset owner, and evidence retention requirement.
2. Preserve logs and volatile evidence before broad remediation.
3. Classify severity by business impact, exploitability, blast radius, and data sensitivity.
4. For suspected web intrusion, first isolate the exposed route or WAF policy, then verify application logs, auth logs, EDR alerts, and recent deployment changes.
5. Produce an action plan with owner, deadline, rollback path, and monitoring query.
