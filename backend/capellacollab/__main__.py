# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import logging
import os

import fastapi
import starlette_prometheus
import uvicorn
from fastapi import middleware, responses
from fastapi.middleware import cors

import capellacollab.sessions.metrics

# This import statement is required and should not be removed! (Alembic will not work otherwise)
from capellacollab.config import config
from capellacollab.core import logging as core_logging
from capellacollab.core.database import engine, migration
from capellacollab.routes import router, status
from capellacollab.sessions import idletimeout, operators

handlers: list[logging.Handler] = [
    logging.StreamHandler(),
    core_logging.CustomTimedRotatingFileHandler(
        str(config["logging"]["logPath"]) + "backend.log"
    ),
]

for handler in handlers:
    handler.setFormatter(core_logging.CustomFormatter())

logging.basicConfig(level=config["logging"]["level"], handlers=handlers)


async def startup():
    migration.migrate_db(engine, config["database"]["url"])
    logging.info("Migrations done - Server is running")

    # This is needed to load the Kubernetes configuration at startup
    operators.get_operator()

    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").disabled = True
    logging.getLogger("requests_oauthlib.oauth2_session").setLevel("INFO")
    logging.getLogger("kubernetes.client.rest").setLevel("INFO")


async def shutdown():
    logging.getLogger("uvicorn.access").disabled = False
    logging.getLogger("uvicorn.error").disabled = False


async def schedule_termination_of_idle_sessions():
    if os.getenv("DISABLE_SESSION_TIMEOUT", "") not in ("true", "1", "t"):
        await idletimeout.terminate_idle_sessions_in_background()


app = fastapi.FastAPI(
    title="Capella Collaboration",
    on_startup=[
        startup,
        schedule_termination_of_idle_sessions,
        capellacollab.sessions.metrics.register,
    ],
    middleware=[
        middleware.Middleware(
            cors.CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["POST", "GET", "OPTIONS", "DELETE", "PUT", "PATCH"],
            allow_headers=["*"],
        ),
        middleware.Middleware(core_logging.AttachTraceIdMiddleware),
        middleware.Middleware(core_logging.AttachUserNameMiddleware),
        middleware.Middleware(core_logging.LogExceptionMiddleware),
        middleware.Middleware(core_logging.LogRequestsMiddleware),
        middleware.Middleware(starlette_prometheus.PrometheusMiddleware),
    ],
    on_shutdown=[shutdown],
)


@app.exception_handler(500)
async def handle_exceptions(request: fastapi.Request, exc: Exception):
    # pylint: disable=unused-argument
    """
    A custom exception handler is required, otherwise no CORS headers are included
    in the case of exceptions.
    https://github.com/encode/starlette/issues/1175
    """
    cors_middleware = cors.CORSMiddleware(
        app=app,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["POST", "GET", "OPTIONS", "DELETE", "PUT", "PATCH"],
        allow_headers=["*"],
    )

    response = responses.JSONResponse(
        status_code=500, content={"body": "Internal Server Error"}
    )
    response.headers.update(cors_middleware.simple_headers)

    return response


@app.get("/healthcheck", tags=["Healthcheck"])
async def healthcheck():
    return {"status": "alive"}


app.add_route("/metrics", starlette_prometheus.metrics)

app.include_router(status.router, prefix="", tags=["Status"])
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app)
