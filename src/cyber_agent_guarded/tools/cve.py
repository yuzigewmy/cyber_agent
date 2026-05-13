from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class VulnerabilityRecord:
    cve_id: str
    description: str
    published: str | None = None
    cvss: float | None = None
    kev: bool = False
    epss: float | None = None
    source: str = "nvd"


class CVEClient:
    """Safe vulnerability intelligence client.

    The client enriches product/version signals with defensive metadata. It does
    not retrieve or output exploit code.
    """

    def __init__(
        self,
        nvd_api_key: str | None = None,
        epss_url: str = "https://api.first.org/data/v1/epss",
        cisa_kev_url: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        timeout: float = 15.0,
    ) -> None:
        self.nvd_api_key = nvd_api_key or os.getenv("NVD_API_KEY")
        self.epss_url = epss_url
        self.cisa_kev_url = cisa_kev_url
        self.timeout = timeout

    def search_nvd_keyword(self, keyword: str, limit: int = 10) -> list[VulnerabilityRecord]:
        headers = {"apiKey": self.nvd_api_key} if self.nvd_api_key else {}
        params = {"keywordSearch": keyword, "resultsPerPage": min(limit, 20)}
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        records: list[VulnerabilityRecord] = []
        for item in data.get("vulnerabilities", [])[:limit]:
            cve = item.get("cve", {})
            metrics = cve.get("metrics", {})
            cvss = self._extract_cvss(metrics)
            description = ""
            for desc in cve.get("descriptions", []):
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            records.append(
                VulnerabilityRecord(
                    cve_id=cve.get("id", "unknown"),
                    description=description[:800],
                    published=cve.get("published"),
                    cvss=cvss,
                )
            )
        return records

    def fetch_cisa_kev_ids(self) -> set[str]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.cisa_kev_url)
            response.raise_for_status()
            data = response.json()
        return {item.get("cveID", "") for item in data.get("vulnerabilities", []) if item.get("cveID")}

    def enrich_epss(self, records: list[VulnerabilityRecord]) -> list[VulnerabilityRecord]:
        ids = [r.cve_id for r in records if r.cve_id]
        if not ids:
            return records
        params = {"cve": ",".join(ids)}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.epss_url, params=params)
            response.raise_for_status()
            data = response.json()
        epss_by_id: dict[str, float] = {}
        for row in data.get("data", []):
            try:
                epss_by_id[row["cve"]] = float(row["epss"])
            except (KeyError, ValueError, TypeError):
                continue
        for record in records:
            record.epss = epss_by_id.get(record.cve_id)
        return records

    def rank(self, records: list[VulnerabilityRecord], kev_ids: set[str] | None = None) -> list[VulnerabilityRecord]:
        kev_ids = kev_ids or set()
        for record in records:
            record.kev = record.cve_id in kev_ids

        def score(record: VulnerabilityRecord) -> float:
            value = record.cvss or 0.0
            if record.kev:
                value += 10.0
            if record.epss is not None:
                value += record.epss * 5.0
            return value

        return sorted(records, key=score, reverse=True)

    @staticmethod
    def _extract_cvss(metrics: dict[str, Any]) -> float | None:
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            values = metrics.get(key) or []
            if values:
                try:
                    return float(values[0]["cvssData"]["baseScore"])
                except (KeyError, ValueError, TypeError):
                    continue
        return None
