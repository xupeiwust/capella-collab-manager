# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import json
import logging

import requests
from sqlalchemy import orm

import capellacollab.settings.modelsources.t4c.repositories.interface as t4c_repository_interface
from capellacollab.core.authentication import injectables as auth_injectables
from capellacollab.projects.toolmodels.modelsources.git import (
    models as git_models,
)
from capellacollab.projects.toolmodels.modelsources.t4c import (
    models as t4c_models,
)
from capellacollab.sessions import operators
from capellacollab.users import models as users_models

from . import crud, exceptions, models

log = logging.getLogger(__name__)


def get_environment(
    git_model: git_models.DatabaseGitModel,
    t4c_model: t4c_models.DatabaseT4CModel,
    t4c_username: str,
    t4c_password: str,
    include_commit_history: bool = False,
) -> dict[str, str]:
    env = {
        "GIT_REPO_URL": git_model.path,
        "GIT_REPO_BRANCH": git_model.revision,
        "GIT_USERNAME": git_model.username,
        "GIT_PASSWORD": git_model.password,
        "T4C_REPO_HOST": t4c_model.repository.instance.host,
        "T4C_REPO_PORT": str(t4c_model.repository.instance.port),
        "T4C_REPO_NAME": t4c_model.repository.name,
        "T4C_PROJECT_NAME": t4c_model.name,
        "T4C_USERNAME": t4c_username,
        "T4C_PASSWORD": t4c_password,
        "LOG_LEVEL": "INFO",
        "INCLUDE_COMMIT_HISTORY": json.dumps(include_commit_history),
    }

    if http_port := t4c_model.repository.instance.http_port:
        env |= {
            "HTTP_LOGIN": t4c_model.repository.instance.username,
            "HTTP_PASSWORD": t4c_model.repository.instance.password,
            "HTTP_PORT": str(http_port),
            "CONNECTION_TYPE": "http",
        }
    else:
        env |= env | {
            "T4C_CDO_PORT": str(t4c_model.repository.instance.cdo_port),
            "CONNECTION_TYPE": "telnet",
        }

    return env


def delete_pipeline(
    db: orm.Session,
    pipeline: models.DatabaseBackup,
    username: str,
    force: bool,
):
    try:
        t4c_repository_interface.remove_user_from_repository(
            pipeline.t4c_model.repository.instance,
            pipeline.t4c_model.repository.name,
            pipeline.t4c_username,
        )
    except requests.RequestException:
        log.error(
            "Error during the deletion of user %s in t4c",
            pipeline.t4c_username,
            exc_info=True,
        )

        if not (
            force
            and auth_injectables.RoleVerification(
                required_role=users_models.Role.ADMIN, verify=False
            )(username=username, db=db)
        ):
            raise exceptions.PipelineOperationFailedT4CServerUnreachable(
                exceptions.PipelineOperation.DELETE
            )

    if pipeline.run_nightly:
        operators.get_operator().delete_cronjob(pipeline.k8s_cronjob_id)

    crud.delete_pipeline(db, pipeline)
