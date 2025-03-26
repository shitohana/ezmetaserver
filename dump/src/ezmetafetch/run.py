import asyncio
import pandas as pd

from .base import Base
from .tasks import SearchTask, FetchTask
from .utils import run_coros_limited


def main():
    model = Base.from_args()
    assert model.terms_list or model.ids_list, ValueError("Either terms file or ids file need to be specified.")
    
    async def body():
        assert model.config is not None, ValueError
        uids = set(model.ids_list)
        if model.terms_list:
            coros = [
                SearchTask(
                    term=" OR ".join(model.terms_list[i : i + model.config.search.terms_per_request]),
                    db=model.db,
                    retmax=model.config.search.ids_per_request,
                    api_key=model.config.http.api_key
                    ).dump(with_model=model)
                for i in range(0, len(model.terms_list), model.config.search.terms_per_request)
            ]
            search_res = set.union(*await run_coros_limited(coros, model.config.http.rate_limit))
            uids |= search_res
            
            with (model.output / "search_uids.txt").open("w") as file:
                file.write("\n".join(map(str, search_res)))
        
        uids = list(uids)
        coros = [
            FetchTask(
                batch_uids=uids[i : i + model.config.fetch.ids_per_request], 
                db=model.db,
                api_key=model.config.http.api_key
                ).dump(with_model=model) 
            for i in range(0, len(uids), model.config.fetch.ids_per_request)
        ]
        fetch_res = await run_coros_limited(coros, model.config.http.rate_limit)
        df = pd.concat(fetch_res)
        df.to_csv(model.output / "fetch_result.tsv", sep="\t", index=False)
            
    asyncio.run(body())