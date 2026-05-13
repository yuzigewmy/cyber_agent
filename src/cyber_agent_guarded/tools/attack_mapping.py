from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttackPathNode:
    asset: str
    exposure: str
    likely_tactics: list[str]
    validation_boundary: str


class AttackPathModeler:
    """Produces high-level, non-operational attack path hypotheses."""

    def model(self, assets: list[str], observations: list[str]) -> list[AttackPathNode]:
        nodes: list[AttackPathNode] = []
        obs_text = " ".join(observations).lower()
        for asset in assets:
            tactics = ["Reconnaissance", "Initial Access"]
            exposure = "Unknown exposure; verify via approved inventory."
            if any(word in asset.lower() for word in ["api", "gateway", "nginx", "web"]):
                exposure = "Internet-facing application boundary."
                tactics.extend(["Execution risk through application flaws", "Defense validation"])
            if "kubernetes" in obs_text or "k8s" in obs_text or "container" in obs_text:
                tactics.append("Container and orchestration control-plane review")
            nodes.append(
                AttackPathNode(
                    asset=asset,
                    exposure=exposure,
                    likely_tactics=tactics,
                    validation_boundary="Manual approval required before intrusive validation.",
                )
            )
        return nodes
