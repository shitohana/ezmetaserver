from typing import List, Optional
from xml.etree import ElementTree

import httpx
import pandas as pd
import xmltodict

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
DATABASE = "sra"


async def search_ncbi_ids(
    client: httpx.AsyncClient,
    terms: List[str],
    max_results: int,
    api_key: Optional[str] = None
) -> List[int]:
    """Search NCBI for IDs matching the given terms."""
    search_term = " OR ".join(terms)
    search_params = {
        "db": DATABASE,
        "term": search_term,
        "retmode": "json",
        "retmax": max_results
    }

    if api_key:
        search_params["api_key"] = api_key

    search_response = await client.post(NCBI_ESEARCH_URL, data=search_params)
    search_response.raise_for_status()
    search_data = search_response.json()

    return [int(id_str) for id_str in search_data.get("esearchresult", {}).get("idlist", [])]


async def fetch_metadata(
    client: httpx.AsyncClient,
    ids: List[int],
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """Fetch metadata for the given IDs from NCBI."""
    fetch_params = {
        "db": DATABASE,
        "id": ",".join(map(str, ids)),
        "retmode": "xml"
    }

    if api_key:
        fetch_params["api_key"] = api_key

    fetch_response = await client.post(NCBI_EFETCH_URL, data=fetch_params)
    fetch_response.raise_for_status()

    # Parse XML
    root = ElementTree.fromstring(fetch_response.text)
    records = root.findall("./*")

    dataframes = []
    for record in records:
        record_dict = {}
        for child in record.findall("./*"):
            record_dict.update(xmltodict.parse(
                ElementTree.tostring(child), process_namespaces=True
            ))
        dataframes.append(pd.json_normalize(record_dict))

    return pd.concat(dataframes) if dataframes else pd.DataFrame()
