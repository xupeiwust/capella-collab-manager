# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from fastapi import testclient
from sqlalchemy import orm

import capellacollab.sessions.operators
from capellacollab.projects import models as projects_models
from capellacollab.projects.toolmodels import crud as toolmodels_crud
from capellacollab.projects.toolmodels import models as toolmodels_models
from capellacollab.tools import crud as tools_crud
from capellacollab.tools import models as tools_models


class MockOperator:
    _created_volumes = 0
    _deleted_volumes = 0

    def create_persistent_volume(
        self, name: str, size: str, labels: dict[str, str] = None
    ):
        self._created_volumes += 1

    def delete_persistent_volume(self, name: str):
        self._deleted_volumes += 1


@pytest.fixture(name="jupyter_tool")
def fixture_jupyter_tool(db: orm.Session) -> tools_models.DatabaseTool:
    return tools_crud.get_tool_by_name(db, "Jupyter")


@pytest.fixture(name="jupyter_model")
def fixture_jupyter_model(
    db: orm.Session,
    project: projects_models.DatabaseProject,
    jupyter_tool: tools_models.DatabaseTool,
) -> toolmodels_models.CapellaModel:
    jupyter_model = toolmodels_models.PostCapellaModel(
        name="Jupyter test",
        description="",
        tool_id=jupyter_tool.id,
    )
    return toolmodels_crud.create_model(
        db,
        project,
        jupyter_model,
        tool=jupyter_tool,
        configuration={"workspace": "test"},
    )


@pytest.fixture(name="mockoperator")
def fixture_mockoperator(monkeypatch: pytest.MonkeyPatch):
    mockoperator = MockOperator()
    monkeypatch.setattr(
        capellacollab.sessions.operators, "get_operator", lambda: mockoperator
    )
    return mockoperator


@pytest.mark.usefixtures("project_manager")
def test_creation_of_jupyter_fileshare(
    client: testclient.TestClient,
    project: projects_models.DatabaseProject,
    jupyter_tool: tools_models.DatabaseTool,
    mockoperator: MockOperator,
):
    response = client.post(
        f"/api/v1/projects/{project.slug}/models",
        json={
            "name": "Jupyter test",
            "description": "",
            "tool_id": jupyter_tool.id,
        },
    )

    assert response.is_success
    assert mockoperator._created_volumes == 1


@pytest.mark.usefixtures("project_manager")
def test_deletion_of_jupyter_fileshare(
    client: testclient.TestClient,
    project: projects_models.DatabaseProject,
    jupyter_model: toolmodels_models.CapellaModel,
    mockoperator: MockOperator,
):
    response = client.delete(
        f"/api/v1/projects/{project.slug}/models/{jupyter_model.slug}"
    )

    assert response.is_success
    assert mockoperator._deleted_volumes == 1
