import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .drill_workflow import run_leaked_key_drill
from .infrai_client import InfraiClient, InfraiError
from .models import DrillRequest, DrillResult

app = FastAPI(title="Property key drill")


@app.post("/drills/leaked-key", response_model=DrillResult)
async def leaked_key_drill(request: DrillRequest) -> DrillResult | JSONResponse:
    client = InfraiClient(api_key=os.environ["INFRAI_API_KEY"])
    try:
        return await run_leaked_key_drill(client, request)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        return JSONResponse(
            status_code=client_status,
            content={"ok": False, "error": exc.detail},
        )
    finally:
        await client.close()
