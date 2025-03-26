from flask import Flask, request, jsonify, abort
from fastapi import FastAPI, HTTPException
import asyncio
from typing import List
import pandas as pd
import json

from ezmetafetch import SearchTask, FetchTask, run_coros_limited, ConfigModel, Base
from schema import EzMetaFetchResponse, EzMetaFetchRequest

app = FastAPI(
    title="EzMetaFetch API",
    description="API for fetching metadata from NCBI databases",
    root_path="/api/v1/dump"
)

@app.post("/api/ezmetafetch", response_model=EzMetaFetchResponse)
async def fetch_metadata(request: EzMetaFetchRequest):
    """Fetch metadata from NCBI databases using ezmetafetch"""

    # Validate input
    if not request.terms and not request.ids:
        raise HTTPException(
            status_code=400,
            detail="Either terms or ids must be provided"
        )

    # Create configuration
    config = ConfigModel(
        http={"api_key": request.api_key, "rate_limit": 10 if request.api_key else 3},
        search={"ids_per_request": min(100, request.max_results)},
        fetch={"ids_per_request": min(100, request.max_results)}
    )

    # Initialize base model
    model = Base(
        db=request.db,
        config=config
    )

    # Run the search and fetch operations
    try:
        # Search for IDs if terms are provided
        search_ids = set()
        if request.terms:
            coros = [
                SearchTask(
                    term=" OR ".join(request.terms),
                    db=request.db,
                    retmax=request.max_results,
                    api_key=request.api_key
                ).dump(with_model=model)
            ]
            search_results = await run_coros_limited(coros, model.config.http.rate_limit)
            search_ids = set.union(*search_results)

        # Combine with provided IDs if any
        all_ids = list(search_ids.union(set(request.ids or [])))[:request.max_results]
        print(f"Search IDs: {all_ids}")

        # Fetch metadata for all IDs
        if all_ids:
            coros = [
                FetchTask(
                    batch_uids=all_ids,
                    db=request.db,
                    api_key=request.api_key
                ).dump(with_model=model)
            ]
            fetch_results = await run_coros_limited(coros, model.config.http.rate_limit)
            metadata_df = pd.concat(fetch_results)

            # Convert to list of dicts for JSON serialization
            metadata_records = json.loads(metadata_df.to_json(orient="records"))

            return EzMetaFetchResponse(
                search_ids=search_ids,
                ids=all_ids,
                metadata=metadata_records,
                status="success",
                message=f"Retrieved metadata for {len(metadata_records)} records"
            )
        else:
            return EzMetaFetchResponse(
                search_ids=[],
                metadata=[],
                status="success",
                message="No records found matching the criteria"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
def health_check():
    return {"status": "healthy"}
