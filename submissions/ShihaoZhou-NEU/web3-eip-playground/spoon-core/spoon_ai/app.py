from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spoon_ai.nft.service import app as nft_app
from spoon_ai.tutor.service import app as tutor_app


# Load .env automatically for local/demo usage, matching repository guidance.
load_dotenv(override=True)


app = FastAPI(title="Spoon API", version="0.1.0")


def _configure_cors(application: FastAPI) -> None:
    raw_origins = os.getenv("TUTOR_CORS_ORIGINS", "*")
    origins = [o.strip() for o in raw_origins.split(",") if o.strip()] or ["*"]
    allow_credentials = origins != ["*"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_configure_cors(app)


app.include_router(tutor_app.router)
app.include_router(nft_app.router)
