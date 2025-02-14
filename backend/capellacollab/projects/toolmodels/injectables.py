# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

import fastapi
from fastapi import status
from sqlalchemy import orm

from capellacollab.core import database
from capellacollab.projects import injectables as projects_injectables
from capellacollab.projects import models as projects_models

from . import crud, models


def get_existing_capella_model(
    model_slug: str,
    project: projects_models.DatabaseProject = fastapi.Depends(
        projects_injectables.get_existing_project
    ),
    db: orm.Session = fastapi.Depends(database.get_db),
) -> models.DatabaseCapellaModel:
    model = crud.get_model_by_slugs(db, project.slug, model_slug)
    if not model:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "reason": f"The model having the name {model_slug} of the project {project.slug} was not found.",
                "technical": f"No model with {model_slug} found in the project {project.slug}.",
            },
        )
    return model
