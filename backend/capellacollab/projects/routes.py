# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import logging
import typing as t

from fastapi import APIRouter, Depends, HTTPException
from slugify import slugify
from sqlalchemy.orm import Session

from capellacollab.core.authentication.database import (
    ProjectRoleVerification,
    RoleVerification,
    get_db,
)
from capellacollab.core.authentication.jwt_bearer import JWTBearer
from capellacollab.core.logging import get_logger
from capellacollab.projects import crud
from capellacollab.projects.models import (
    DatabaseProject,
    PatchProject,
    PostProjectRequest,
    Project,
)
from capellacollab.projects.toolmodels.injectables import get_existing_project
from capellacollab.projects.users import crud as users_crud
from capellacollab.projects.users.models import (
    ProjectUserPermission,
    ProjectUserRole,
)
from capellacollab.sessions.routes import project_router as router_sessions
from capellacollab.users.injectables import get_own_user
from capellacollab.users.models import DatabaseUser, Role

from .toolmodels.routes import router as router_models
from .users.routes import router as router_users

logger = logging.getLogger(__name__)
router = APIRouter(
    dependencies=[Depends(RoleVerification(required_role=Role.USER))]
)


@router.get(
    "/",
    response_model=t.List[Project],
    tags=["Projects"],
)
def get_projects(
    user: DatabaseUser = Depends(get_own_user),
    db: Session = Depends(get_db),
    token=Depends(JWTBearer()),
    log: logging.LoggerAdapter = Depends(get_logger),
) -> t.List[DatabaseProject]:
    log.debug("Fetching all projects")
    if RoleVerification(required_role=Role.ADMIN, verify=False)(token, db):
        return crud.get_all_projects(db)

    return [association.project for association in user.projects]


@router.patch(
    "/{project_slug}",
    response_model=Project,
    tags=["Projects"],
    dependencies=[
        Depends(ProjectRoleVerification(required_role=ProjectUserRole.MANAGER))
    ],
)
def update_project(
    patch_project: PatchProject,
    project: DatabaseProject = Depends(get_existing_project),
    database: Session = Depends(get_db),
) -> DatabaseProject:
    new_slug = slugify(patch_project.name)
    if (
        crud.get_project_by_slug(database, new_slug)
        and project.slug != new_slug
    ):
        raise HTTPException(
            409,
            {
                "reason": "A project with a similar name already exists.",
                "technical": "Slug already used",
            },
        )
    return crud.update_project(database, project, patch_project)


@router.get(
    "/{project_slug}",
    response_model=Project,
    tags=["Projects"],
    dependencies=[
        Depends(ProjectRoleVerification(required_role=ProjectUserRole.USER))
    ],
)
def get_project_by_slug(
    db_project: DatabaseProject = Depends(get_existing_project),
    user: DatabaseUser = Depends(get_own_user),
    log=Depends(get_logger),
) -> DatabaseProject:
    log.info(f"{user.name} gets the project {db_project.name}")
    return db_project


@router.post("/", response_model=Project, tags=["Projects"])
def create_project(
    post_project: PostProjectRequest,
    user: DatabaseUser = Depends(get_own_user),
    db: Session = Depends(get_db),
) -> DatabaseProject:
    if crud.get_project_by_slug(db, slugify(post_project.name)):
        raise HTTPException(
            409,
            {
                "reason": "A project with a similar name already exists.",
                "technical": "Slug already used",
            },
        )

    new_project = crud.create_project(
        db, post_project.name, post_project.description
    )

    if user.role != Role.ADMIN:
        users_crud.add_user_to_project(
            db,
            new_project,
            user,
            ProjectUserRole.MANAGER,
            ProjectUserPermission.WRITE,
        )

    return new_project


@router.delete(
    "/{project_slug}",
    tags=["Projects"],
    status_code=204,
    dependencies=[Depends(RoleVerification(required_role=Role.ADMIN))],
)
def delete_project(
    project: DatabaseProject = Depends(get_existing_project),
    db: Session = Depends(get_db),
):
    if project.models:
        raise HTTPException(
            409, {"reason": "The project still has models assigned to it"}
        )
    users_crud.delete_users_from_project(db, project)
    crud.delete_project(db, project)


router.include_router(
    router_users, tags=["Projects"], prefix="/{project_slug}/users"
)
router.include_router(
    router_models, prefix="/{project_slug}/models", tags=["Projects - Models"]
)
router.include_router(
    router_sessions,
    prefix="/{project_slug}/sessions",
    tags=["Projects - Sessions"],
)
