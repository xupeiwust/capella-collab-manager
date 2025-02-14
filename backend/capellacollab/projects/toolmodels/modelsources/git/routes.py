# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import urllib.parse

import fastapi
import requests
from fastapi import status
from sqlalchemy import orm

from capellacollab.core import database
from capellacollab.core.authentication import injectables as auth_injectables
from capellacollab.projects.toolmodels import (
    injectables as toolmodels_injectables,
)
from capellacollab.projects.toolmodels import models as toolmodels_models
from capellacollab.projects.toolmodels.backups import crud as backups_crud
from capellacollab.projects.users import models as projects_users_models
from capellacollab.settings.modelsources.git import core as git_core
from capellacollab.settings.modelsources.git import crud as git_crud
from capellacollab.settings.modelsources.git import models as git_models

from . import crud, injectables, models

router = fastapi.APIRouter()
log = logging.getLogger(__name__)


def verify_path_prefix(db: orm.Session, path: str):
    if not (git_instances := git_crud.get_git_instances(db)):
        return

    unquoted_path = urllib.parse.unquote(path)
    if resolved_path := requests.Request("GET", unquoted_path).prepare().url:
        for git_instance in git_instances:
            unquoted_git_url = urllib.parse.unquote(git_instance.url)
            resolved_git_url = (
                requests.Request("GET", unquoted_git_url).prepare().url
            )

            if resolved_git_url and resolved_path.startswith(resolved_git_url):
                return

    raise fastapi.HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "err_code": "no_git_instance_with_prefix_found",
            "reason": "There exist no git instance having the resolved path as prefix. Please check whether you correctly selected a git instance.",
        },
    )


@router.post("/validate/path", response_model=bool)
def validate_path(
    url: str = fastapi.Body(),
    db: orm.Session = fastapi.Depends(database.get_db),
) -> bool:
    try:
        verify_path_prefix(db, url)
        return True
    except Exception:
        return False


@router.get("", response_model=list[models.GitModel])
def get_git_models(
    capella_model: toolmodels_models.DatabaseCapellaModel = fastapi.Depends(
        toolmodels_injectables.get_existing_capella_model
    ),
) -> list[models.DatabaseGitModel]:
    return capella_model.git_models


@router.get(
    "/{git_model_id}",
    response_model=models.GitModel,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ],
)
def get_git_model_by_id(
    git_model: models.DatabaseGitModel = fastapi.Depends(
        injectables.get_existing_git_model
    ),
) -> models.DatabaseGitModel:
    return git_model


@router.get(
    "/primary/revisions",
    response_model=git_models.GetRevisionsResponseModel,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ],
)
async def get_revisions_of_primary_git_model(
    primary_git_model: models.DatabaseGitModel = fastapi.Depends(
        injectables.get_existing_primary_git_model
    ),
) -> git_models.GetRevisionsResponseModel:
    return await git_core.get_remote_refs(
        primary_git_model.path,
        primary_git_model.username,
        primary_git_model.password,
        default=primary_git_model.revision,
    )


@router.post(
    "/{git_model_id}/revisions",
    response_model=git_models.GetRevisionsResponseModel,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.USER
            )
        )
    ],
)
async def get_revisions_with_model_credentials(
    url: str = fastapi.Body(),
    git_model: models.DatabaseGitModel = fastapi.Depends(
        injectables.get_existing_git_model
    ),
):
    return await git_core.get_remote_refs(
        url, git_model.username, git_model.password
    )


@router.post(
    "",
    response_model=models.GitModel,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ],
)
def create_git_model(
    post_git_model: models.PostGitModel,
    capella_model: toolmodels_models.DatabaseCapellaModel = fastapi.Depends(
        toolmodels_injectables.get_existing_capella_model
    ),
    db: orm.Session = fastapi.Depends(database.get_db),
) -> models.DatabaseGitModel:
    verify_path_prefix(db, post_git_model.path)

    new_git_model = crud.add_git_model_to_capellamodel(
        db, capella_model, post_git_model
    )
    return new_git_model


@router.put(
    "/{git_model_id}",
    response_model=models.GitModel,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ],
)
def update_git_model_by_id(
    patch_git_model: models.PatchGitModel,
    db_git_model: models.DatabaseGitModel = fastapi.Depends(
        injectables.get_existing_git_model
    ),
    db: orm.Session = fastapi.Depends(database.get_db),
) -> models.DatabaseGitModel:
    verify_path_prefix(db, patch_git_model.path)
    return crud.update_git_model(db, db_git_model, patch_git_model)


@router.delete(
    "/{git_model_id}",
    status_code=204,
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ],
)
def delete_git_model_by_id(
    db_git_model: models.DatabaseGitModel = fastapi.Depends(
        injectables.get_existing_git_model
    ),
    db: orm.Session = fastapi.Depends(database.get_db),
):
    if backups_crud.get_pipelines_for_git_model(db, db_git_model):
        raise fastapi.HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "err_code": "git_model_used_for_backup",
                "reason": "The git model can't be deleted: it's used for backup jobs",
            },
        )

    crud.delete_git_model(db, db_git_model)
