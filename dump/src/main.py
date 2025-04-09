import httpx
from fastapi import FastAPI, HTTPException, Query

from requests import NCBI_ESEARCH_URL, DATABASE, search_ncbi_ids, fetch_metadata
from rename import select_and_rename_common_columns
from schema import EzMetaFetchResponse, EzMetaFetchRequest


app = FastAPI(
    title="EzMetaFetch API",
    description="API for fetching metadata from NCBI databases",
    root_path="/api/v1/dump"
)


@app.post("/fetch", response_model=EzMetaFetchResponse)
async def fetch_metadata_handler(request: EzMetaFetchRequest):
    """Fetch metadata from NCBI databases using ezmetafetch"""

    # Validate input
    if not request.terms and not request.ids:
        raise HTTPException(
            status_code=400,
            detail="Either terms or ids must be provided"
        )

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Search for IDs if terms are provided
            search_ids = await search_ncbi_ids(
                client,
                request.terms,
                request.max_results,
                request.api_key
            ) if request.terms else []

            # Combine with provided IDs if any
            provided_ids = request.ids or []
            all_ids = list(set(search_ids).union(set(provided_ids)))[:request.max_results]

            # Step 2: Fetch metadata for all IDs
            if all_ids:
                data = await fetch_metadata(client, all_ids, request.api_key)

                if not data.empty:
                    result = select_and_rename_common_columns(data)
                    metadata_dict = result.to_dict('split')

                    return EzMetaFetchResponse(
                        search_ids=search_ids,
                        ids=all_ids,
                        metadata=metadata_dict,
                        status="success",
                        message=f"Retrieved metadata for {len(result)} records"
                    )

            # Return empty result if no IDs or no data found
            return EzMetaFetchResponse(
                search_ids=search_ids,
                ids=all_ids if all_ids else [],
                metadata={},
                status="success",
                message="No records found matching the criteria"
            )

    except httpx.HTTPError as e:
        status_code = 500
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code

        raise HTTPException(
            status_code=status_code,
            detail=f"HTTP error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/peek")
async def peek(term: str = Query(..., description="Search term to query NCBI")):
    """Get count of records matching a term in NCBI SRA database"""
    try:
        url = f"{NCBI_ESEARCH_URL}?db={DATABASE}&term={term}&rettype=count&retmode=json"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            count = data.get("esearchresult", {}).get("count", "0")
            return {"count": count}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching count from NCBI: {str(e)}"
        )
