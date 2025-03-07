# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0


import io
import logging
import tarfile
import typing as t

import fastapi
from fastapi import responses

from capellacollab.core import responses as core_responses
from capellacollab.permissions import injectables as permissions_injectables
from capellacollab.permissions import models as permissions_models
from capellacollab.sessions import injectables as sessions_injectables
from capellacollab.sessions import models as sessions_models
from capellacollab.sessions import operators

from . import exceptions, models

router = fastapi.APIRouter()
log = logging.getLogger(__name__)


@router.get(
    "",
    response_model=models.FileTree,
    dependencies=[
        fastapi.Depends(
            permissions_injectables.PermissionValidation(
                required_scope=permissions_models.GlobalScopes(
                    user=permissions_models.UserScopes(
                        sessions={permissions_models.UserTokenVerb.GET}
                    )
                )
            ),
        )
    ],
)
def list_files(
    show_hidden: bool,
    session: t.Annotated[
        sessions_models.DatabaseSession,
        fastapi.Depends(sessions_injectables.get_existing_session),
    ],
):
    try:
        return operators.get_operator().list_files(
            session.id, "/workspace", show_hidden
        )
    except Exception as e:
        log.exception("Loading of files for session %s failed", session.id)
        raise exceptions.SessionFileLoadingFailedError() from e


@router.post(
    "",
    status_code=204,
    dependencies=[
        fastapi.Depends(
            permissions_injectables.PermissionValidation(
                required_scope=permissions_models.GlobalScopes(
                    user=permissions_models.UserScopes(
                        sessions={permissions_models.UserTokenVerb.UPDATE}
                    )
                )
            ),
        )
    ],
)
def upload_files(
    files: list[fastapi.UploadFile],
    session: t.Annotated[
        sessions_models.DatabaseSession,
        fastapi.Depends(sessions_injectables.get_existing_session),
    ],
):
    tar_bytesio = io.BytesIO()

    with tarfile.TarFile(
        name="upload.tar", mode="w", fileobj=tar_bytesio
    ) as tar:
        size = sum(len(file.file.read()) for file in files)
        if size > 31457280:
            raise exceptions.FileSizeExceededError()

        for file in files:
            file.file.seek(0)

            assert file.filename
            tar.addfile(
                tar.gettarinfo(arcname=file.filename, fileobj=file.file),
                fileobj=file.file,
            )

    tar_bytesio.seek(0)
    tar_bytes = tar_bytesio.read()

    operators.get_operator().upload_files(session.id, tar_bytes)


@router.delete(
    "",
    status_code=204,
    dependencies=[
        fastapi.Depends(
            permissions_injectables.PermissionValidation(
                required_scope=permissions_models.GlobalScopes(
                    user=permissions_models.UserScopes(
                        sessions={permissions_models.UserTokenVerb.UPDATE}
                    )
                )
            ),
        )
    ],
)
def delete_file(
    path: str,
    session: t.Annotated[
        sessions_models.DatabaseSession,
        fastapi.Depends(sessions_injectables.get_existing_session),
    ],
):
    operators.get_operator().delete_file(session.id, path)


@router.get(
    "/download",
    response_class=responses.StreamingResponse,
    responses=core_responses.ZIPFileResponse.responses,
    dependencies=[
        fastapi.Depends(
            permissions_injectables.PermissionValidation(
                required_scope=permissions_models.GlobalScopes(
                    user=permissions_models.UserScopes(
                        sessions={permissions_models.UserTokenVerb.GET}
                    )
                )
            ),
        )
    ],
)
def download_file(
    path: str,
    session: t.Annotated[
        sessions_models.DatabaseSession,
        fastapi.Depends(sessions_injectables.get_existing_session),
    ],
) -> core_responses.ZIPFileResponse:
    return core_responses.ZIPFileResponse(
        operators.get_operator().download_file(session.id, path),
    )
