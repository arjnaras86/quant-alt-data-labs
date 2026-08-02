from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from bs4 import BeautifulSoup

from quantlab.config import settings
from quantlab.http import build_session

SEC_DATA = "https://data.sec.gov"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"


@dataclass(frozen=True)
class Filing:
    ticker: str
    cik: str
    accession_number: str
    filing_date: str
    report_date: str
    form: str
    primary_document: str

    @property
    def accession_compact(self) -> str:
        return self.accession_number.replace("-", "")

    @property
    def document_url(self) -> str:
        return f"{SEC_ARCHIVES}/{int(self.cik)}/{self.accession_compact}/{self.primary_document}"


class SecClient:
    def __init__(self) -> None:
        settings.require_sec()
        self.session = build_session(settings.sec_user_agent, requests_per_second=5)
        self._ticker_map: pd.DataFrame | None = None

    def ticker_map(self) -> pd.DataFrame:
        if self._ticker_map is None:
            payload = self.session.get(SEC_TICKERS).json()
            self._ticker_map = pd.DataFrame(payload.values()).rename(
                columns={"cik_str": "cik", "title": "company"}
            )
            self._ticker_map["ticker"] = self._ticker_map["ticker"].str.upper()
            self._ticker_map["cik"] = self._ticker_map["cik"].astype(str).str.zfill(10)
        return self._ticker_map.copy()

    def cik_for_ticker(self, ticker: str) -> str:
        match = self.ticker_map()[self.ticker_map()["ticker"] == ticker.upper()]
        if match.empty:
            raise ValueError(f"Ticker not found in SEC mapping: {ticker}")
        return str(match.iloc[0]["cik"])

    def recent_filings(self, ticker: str, forms: Iterable[str], limit: int = 20) -> list[Filing]:
        cik = self.cik_for_ticker(ticker)
        payload = self.session.get(f"{SEC_DATA}/submissions/CIK{cik}.json").json()
        recent = pd.DataFrame(payload["filings"]["recent"])
        recent = recent[recent["form"].isin(set(forms))].head(limit)
        return [
            Filing(
                ticker=ticker.upper(),
                cik=cik,
                accession_number=row.accessionNumber,
                filing_date=row.filingDate,
                report_date=row.reportDate,
                form=row.form,
                primary_document=row.primaryDocument,
            )
            for row in recent.itertuples(index=False)
        ]

    def filing_text(self, filing: Filing) -> str:
        html = self.session.get(filing.document_url).text
        soup = BeautifulSoup(html, "xml")
        for node in soup(["script", "style", "table"]):
            node.decompose()
        text = soup.get_text(" ", strip=True)
        return re.sub(r"\s+", " ", text)

    def filing_xml(self, filing: Filing) -> BeautifulSoup:
        index_url = f"{SEC_ARCHIVES}/{int(filing.cik)}/{filing.accession_compact}/index.json"
        index = self.session.get(index_url).json()
        items = index.get("directory", {}).get("item", [])
        candidates = [
            item["name"] for item in items
            if item.get("name", "").lower().endswith(".xml")
            and "filingsummary" not in item.get("name", "").lower()
        ]
        document = candidates[0] if candidates else filing.primary_document.split("/")[-1]
        url = f"{SEC_ARCHIVES}/{int(filing.cik)}/{filing.accession_compact}/{document}"
        content = self.session.get(url).content
        return BeautifulSoup(content, "xml")
