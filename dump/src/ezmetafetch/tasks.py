from typing import Literal
from xml.etree import ElementTree

import aiohttp
import aiohttp.http_exceptions
import aiohttp_retry
from aiohttp_retry.client import _RequestContext
import pandas as pd
import xmltodict
from pydantic import BaseModel, computed_field

from .base import Base


class RequestTask(BaseModel):
    url: str
    params: dict | None

    @computed_field
    @property
    def method(self) -> Literal["GET", "POST"]:
        total_uri = self.url
        if self.params is not None:
            total_uri += "?" + "&".join(key + "=" + str(value) for key, value in self.params.items())
        return "GET" if len(total_uri) < 2000 else "POST"
    
    @computed_field
    @property
    def kwargs(self) -> dict:
        return {("params" if self.method == "GET" else "data"): self.params}

    def run(self, client: aiohttp_retry.RetryClient) -> _RequestContext:
        resp = client.request(self.method, self.url, ssl=False, **self.kwargs)
        return resp

class SearchTask(RequestTask):
    params: dict

    def __init__(self, term: str, db: str, retmax: int, api_key: str | None = None):
        super().__init__(
            url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": db,
                "term": term,
                "retmode": "xml",
                "retmax": retmax,
            } | ({"api_key": api_key} if api_key is not None else {})
        )

    async def dump(self, with_model: Base | None = None):
        with_model = with_model if with_model is not None else Base()
        dumped_ids = set()
        retstart, count = 0, 0
        while True:
            retry_options = aiohttp_retry.ExponentialRetry(attempts=with_model.config.search.max_retries, statuses=set(with_model.config.http.retry_on))
            retry_client = aiohttp_retry.RetryClient(raise_for_status=True, retry_options=retry_options)
            async with retry_client as client, self.run(client) as resp:
                assert resp.ok, aiohttp.http_exceptions.BadStatusLine(str(resp.status))
                assert (xml := ElementTree.fromstring(await resp.text())).tag == "eSearchResult", KeyError("Invalid response XML.")

            count, retmax, new_ids = self.parse_xml(xml)
            retstart += retmax
            dumped_ids |= new_ids

            if retstart >= count:
                break
            self.params = self.params | {"retstart": retstart}

        return dumped_ids

    @staticmethod
    def parse_xml(xml: ElementTree.Element) -> tuple[int, int, set]:
        """Parse search response xml to extract entities

        Args:
            xml (ElementTree.Element): EntrezAPI Search response

        Returns:
            tuple[int, int, set]: tuple of [Count total, retmax, Dumped ids]
        """
        assert (count := xml.find("./Count")) is not None, KeyError
        assert (retmax := xml.find("./RetMax")) is not None, KeyError
        assert (ids := xml.findall("./IdList/*")) is not None, KeyError
        return (
            int(count.text),  # type: ignore
            int(retmax.text),  # type: ignore
            set(int(tag.text) for tag in ids),  # type: ignore
        )


class FetchTask(RequestTask):
    params: dict

    def __init__(self, batch_uids: list[int], db: str, api_key: str | None = None):
        super().__init__(
            url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": db,
                "id": ",".join(map(str, batch_uids)),
                "retmode": "xml",
                "retmax": len(batch_uids),
            } | ({"api_key": api_key} if api_key is not None else {})
        )

    async def dump(self, with_model: Base | None = None):
        with_model = with_model if with_model is not None else Base()
        retry_options = aiohttp_retry.RandomRetry(attempts=with_model.config.fetch.max_retries, statuses=with_model.config.http.retry_on)
        retry_client = aiohttp_retry.RetryClient(raise_for_status=False, retry_options=retry_options)

        async with retry_client as client, self.run(client) as resp:
            assert resp.ok, aiohttp.http_exceptions.BadStatusLine(str(resp.status))
            xml = ElementTree.fromstring(await resp.text())

        records = xml.findall("./*")
        result = []
        for record in records:
            record_dict = dict()
            for child in record.findall("./*"):
                record_dict |= xmltodict.parse(ElementTree.tostring(child), process_namespaces=True)
            record_row = pd.json_normalize(record_dict)
            result.append(record_row)
        return pd.concat(result)