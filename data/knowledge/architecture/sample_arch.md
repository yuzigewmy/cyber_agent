---
source: sample_enterprise_architecture
collection: architecture
sensitivity: internal
---
# Sample enterprise architecture

The production environment has internet-facing API gateways, WAF, Nginx ingress, Kubernetes workloads, Redis cache, MySQL clusters, Kafka, and internal service mesh.

Critical assets:
- api-gateway: internet-facing, routes traffic to web and mobile APIs.
- user-service: handles identity, sessions, and user profile data.
- payment-service: PCI scoped service, strict segmentation required.
- jump-host: administrative access path, MFA required, all sessions logged.

Default containment preferences:
- Prefer WAF rule and traffic shaping before full service shutdown.
- For credential risk, rotate service accounts and invalidate sessions.
- For container risk, cordon node, snapshot image and logs, redeploy from trusted base image.
