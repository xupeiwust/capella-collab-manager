# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import pytest
from sqlalchemy import orm

import capellacollab.projects.models as project_models
import capellacollab.projects.toolmodels.crud as toolmodels_crud
import capellacollab.projects.toolmodels.models as toolmodels_models
import capellacollab.projects.toolmodels.modelsources.git.crud as git_crud
import capellacollab.projects.toolmodels.modelsources.git.models as git_models
import capellacollab.projects.toolmodels.modelsources.t4c.crud as models_t4c_crud
import capellacollab.projects.toolmodels.modelsources.t4c.models as models_t4c_models
import capellacollab.settings.modelsources.t4c.crud as settings_t4c_crud
import capellacollab.settings.modelsources.t4c.models as t4c_models
import capellacollab.settings.modelsources.t4c.repositories.crud as settings_t4c_repositories_crud
import capellacollab.settings.modelsources.t4c.repositories.interface as t4c_repositories_interface
import capellacollab.settings.modelsources.t4c.repositories.models as settings_t4c_repositories_models
import capellacollab.tools.crud as tools_crud
import capellacollab.tools.models as tools_models
from capellacollab.core import credentials


@pytest.fixture(name="capella_tool_version", params=["6.0.0"])
def fixture_capella_tool_version(
    db: orm.Session,
    request: pytest.FixtureRequest,
) -> tools_models.DatabaseVersion:
    return tools_crud.get_version_by_tool_id_version_name(
        db, tools_crud.get_tool_by_name(db, "Capella").id, request.param
    )


@pytest.fixture(name="capella_model")
def fixture_capella_model(
    db: orm.Session,
    project: project_models.DatabaseProject,
    capella_tool_version: tools_models.DatabaseVersion,
) -> toolmodels_models.DatabaseCapellaModel:
    model = toolmodels_models.PostCapellaModel(
        name="test", description="test", tool_id=capella_tool_version.tool.id
    )
    return toolmodels_crud.create_model(
        db, project, model, capella_tool_version.tool, capella_tool_version
    )


@pytest.fixture(name="git_model")
def fixture_git_models(
    db: orm.Session, capella_model: toolmodels_models.DatabaseCapellaModel
) -> git_models.DatabaseGitModel:
    git_model = git_models.PostGitModel(
        path="https://example.com/test/project",
        entrypoint="test/test.aird",
        revision="main",
        username="user",
        password="password",
    )
    return git_crud.add_git_model_to_capellamodel(db, capella_model, git_model)


@pytest.fixture(name="t4c_repository")
def fixture_t4c_repository(
    db: orm.Session,
) -> settings_t4c_repositories_models.DatabaseT4CRepository:
    t4c_instance = settings_t4c_crud.get_t4c_instances(db)[0]
    return settings_t4c_repositories_crud.create_t4c_repository(
        db=db, repo_name="test", instance=t4c_instance
    )


@pytest.fixture(name="t4c_model")
def fixture_t4c_model(
    db: orm.Session,
    capella_model: toolmodels_models.DatabaseCapellaModel,
    t4c_repository: settings_t4c_repositories_models.DatabaseT4CRepository,
) -> models_t4c_models.DatabaseT4CModel:
    return models_t4c_crud.create_t4c_model(
        db, capella_model, t4c_repository, "default"
    )


@pytest.fixture(name="mock_add_user_to_t4c_repository")
def fixture_mock_add_user_to_t4c_repository(monkeypatch: pytest.MonkeyPatch):
    def mock_add_user_to_repository(
        instance: t4c_models.DatabaseT4CInstance,
        repository_name: str,
        username: str,
        password: str = credentials.generate_password(),
        is_admin: bool = False,
    ):
        return {}

    monkeypatch.setattr(
        t4c_repositories_interface,
        "add_user_to_repository",
        mock_add_user_to_repository,
    )
