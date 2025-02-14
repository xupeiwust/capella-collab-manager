# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import pathlib
from urllib import parse

import fastapi
import requests
from fastapi import status

import capellacollab.projects.toolmodels.modelsources.git.injectables as git_injectables
from capellacollab.core import logging as log
from capellacollab.core.authentication import injectables as auth_injectables
from capellacollab.projects.toolmodels.diagrams import models
from capellacollab.projects.toolmodels.modelsources.git.handler import (
    handler as git_handler,
)
from capellacollab.projects.users import models as projects_users_models

router = fastapi.APIRouter(
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.USER
            )
        )
    ],
)


@router.get("", response_model=models.DiagramCacheMetadata)
async def get_diagram_metadata(
    handler: git_handler.GitHandler = fastapi.Depends(
        git_injectables.get_git_handler
    ),
    logger: logging.LoggerAdapter = fastapi.Depends(log.get_request_logger),
):
    try:
        (
            last_updated,
            diagram_metadata_entries,
        ) = await handler.get_file_from_repository_or_artifacts_as_json(
            "diagram_cache/index.json",
            "update_capella_diagram_cache",
            "diagram-cache/" + handler.git_model.revision,
        )
    except requests.exceptions.HTTPError:
        logger.info("Failed fetching diagram metadata", exc_info=True)
        raise fastapi.HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "reason": (
                    "The diagram cache is not configured properly.",
                    "Please contact your diagram cache administrator.",
                ),
            },
        )

    return models.DiagramCacheMetadata(
        diagrams=[
            models.DiagramMetadata.model_validate(diagram_metadata)
            for diagram_metadata in diagram_metadata_entries
        ],
        last_updated=last_updated,
    )


@router.get(
    "/{diagram_uuid_or_filename}", response_class=fastapi.responses.Response
)
async def get_diagram(
    diagram_uuid_or_filename: str,
    handler: git_handler.GitHandler = fastapi.Depends(
        git_injectables.get_git_handler
    ),
    logger: logging.LoggerAdapter = fastapi.Depends(log.get_request_logger),
):
    fileextension = pathlib.PurePosixPath(diagram_uuid_or_filename).suffix
    if fileextension and fileextension.lower() != ".svg":
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"reason": f"File extension {fileextension} not supported"},
        )

    diagram_uuid = pathlib.PurePosixPath(diagram_uuid_or_filename).stem
    try:
        _, diagram = await handler.get_file_from_repository_or_artifacts(
            f"diagram_cache/{parse.quote(diagram_uuid, safe='')}.svg",
            "update_capella_diagram_cache",
            "diagram-cache/" + handler.git_model.revision,
        )
    except requests.exceptions.HTTPError:
        logger.info("Failed fetching diagram", exc_info=True)
        raise fastapi.HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "reason": (
                    "The diagram cache is not configured properly.",
                    "Please contact your diagram cache administrator.",
                ),
            },
        )

    return fastapi.responses.Response(
        content=diagram,
        media_type="image/svg+xml",
    )
