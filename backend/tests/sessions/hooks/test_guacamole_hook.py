# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import re
import uuid

import pytest
import requests
import responses

from capellacollab.sessions import models as sessions_models
from capellacollab.sessions.hooks import guacamole
from capellacollab.sessions.hooks import interface as session_hooks_interface
from capellacollab.tools import models as tools_models
from capellacollab.users import models as users_models


@pytest.fixture(name="session")
def fixture_session() -> sessions_models.DatabaseSession:
    tool = tools_models.DatabaseTool(name="test")
    tool_version = tools_models.DatabaseVersion(tool=tool, name="6.0.0")

    return sessions_models.DatabaseSession(
        id=str(uuid.uuid1()),
        created_at=datetime.datetime.now(),
        type=sessions_models.SessionType.READONLY,
        owner=users_models.DatabaseUser(
            name="test", idp_identifier="test", role=users_models.Role.USER
        ),
        tool=tool_version.tool,
        version=tool_version,
        environment={"CAPELLACOLLAB_SESSION_TOKEN": "token"},
        connection_method_id=tool.config.connection.methods[0].id,
    )


@pytest.fixture(name="guacamole_configuration", autouse=True)
def fixture_guacamole_configuration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        guacamole.GuacamoleIntegration,
        "_baseURI",
        "https://guacamole-mock",
    )

    monkeypatch.setattr(
        guacamole.GuacamoleIntegration,
        "_prefix",
        "https://guacamole-mock/api/session/data/postgresql",
    )


@pytest.fixture(name="guacamole_create_token", params=[200])
def fixture_guacamole_create_token(request: pytest.FixtureRequest):
    responses.post(
        "https://guacamole-mock/api/tokens",
        status=request.param,
        json={
            "authToken": "token",
        },
    )


@pytest.fixture(name="guacamole_delete_user", params=[200])
def fixture_guacamole_delete_user(request: pytest.FixtureRequest):
    responses.add(
        responses.DELETE,
        re.compile(
            r"https://guacamole-mock/api/session/data/postgresql/users/\w*\?token=token"
        ),
        status=request.param,
    )


@pytest.fixture(name="guacamole_apis")
def fixture_guacamole_apis():
    def match_user_creation_body(
        request: requests.PreparedRequest,
    ) -> tuple[bool, str]:
        body = json.dumps(request.body.decode("utf-8"))

        if "username" not in body:
            return False, "Username not in body"

        if "password" not in body:
            return False, "Password not in body"

        if "attributes" not in body:
            return False, "Attributes not in body"

        return True, ""

    # Create Guacamole user
    responses.post(
        "https://guacamole-mock/api/session/data/postgresql/users?token=token",
        status=200,
        match=[match_user_creation_body],
        json={},
    )

    # Create Guacamole connection
    responses.post(
        "https://guacamole-mock/api/session/data/postgresql/connections?token=token",
        status=200,
        json={"identifier": "connection-id"},
    )

    # Assign user to connection
    responses.add(
        responses.PATCH,
        re.compile(
            r"https://guacamole-mock/api/session/data/postgresql/users/\w*/permissions\?token=token"
        ),
        status=200,
    )

    # Delete connection
    responses.delete(
        "https://guacamole-mock/api/session/data/postgresql/connections/connection-id?token=token",
        status=200,
    )


@responses.activate
@pytest.mark.usefixtures(
    "guacamole_create_token", "guacamole_delete_user", "guacamole_apis"
)
def test_guacamole_configuration_hook(
    session: sessions_models.DatabaseSession,
):
    """Test that the Guacamole hook creates a user and a connection"""

    response = guacamole.GuacamoleIntegration().post_session_creation_hook(
        session_id="test",
        db_session=session,
        session={
            "id": "test",
            "port": "8080",
            "created_at": "2021-01-01T00:00:00",
            "host": "test",
        },
        user=users_models.DatabaseUser(
            name="test", idp_identifier="test", role=users_models.Role.USER
        ),
        connection_method=tools_models.GuacamoleConnectionMethod(),
    )

    assert response["config"]["guacamole_username"]
    assert response["config"]["guacamole_password"]
    assert response["config"]["guacamole_connection_id"] == "connection-id"


@responses.activate
@pytest.mark.parametrize("guacamole_create_token", [404], indirect=True)
@pytest.mark.usefixtures(
    "guacamole_create_token", "guacamole_delete_user", "guacamole_apis"
)
def test_fail_if_guacamole_unreachable(
    session: sessions_models.DatabaseSession,
):
    """If Guacamole is unreachable, the session hook will abort the session creation"""

    responses.post(
        "https://guacamole-mock/api/tokens",
        status=404,
        json={
            "authToken": "token",
        },
    )

    with pytest.raises(guacamole.GuacamoleError):
        guacamole.GuacamoleIntegration().post_session_creation_hook(
            session_id="test",
            db_session=session,
            session={
                "id": "test",
                "port": "8080",
                "created_at": "2021-01-01T00:00:00",
                "host": "test",
            },
            user=users_models.DatabaseUser(
                name="test", idp_identifier="test", role=users_models.Role.USER
            ),
            connection_method=tools_models.GuacamoleConnectionMethod(),
        )


@responses.activate
@pytest.mark.usefixtures(
    "guacamole_create_token", "guacamole_delete_user", "guacamole_apis"
)
def test_guacamole_hook_not_executed_for_http_method(
    session: sessions_models.DatabaseSession,
):
    """Skip if connection method is not Guacamole

    If the connection method is not Guacamole, the hook should skip the preparation.
    """

    response = guacamole.GuacamoleIntegration().post_session_creation_hook(
        session_id="test",
        session={
            "id": "test",
            "port": "8080",
            "created_at": "2021-01-01T00:00:00",
            "host": "test",
        },
        db_session=session,
        user=users_models.DatabaseUser(
            name="test", idp_identifier="test", role=users_models.Role.USER
        ),
        connection_method=tools_models.HTTPConnectionMethod(),
    )

    assert session_hooks_interface.PostSessionCreationHookResult() == response


@responses.activate
@pytest.mark.parametrize("guacamole_delete_user", [404], indirect=True)
@pytest.mark.usefixtures(
    "guacamole_create_token", "guacamole_delete_user", "guacamole_apis"
)
def test_skip_guacamole_user_deletion_on_404(
    session: sessions_models.DatabaseSession,
):
    """If the user does not exist, the hook should not fail"""

    response = guacamole.GuacamoleIntegration().post_session_creation_hook(
        session_id="test",
        db_session=session,
        session={
            "id": "test",
            "port": "8080",
            "created_at": "2021-01-01T00:00:00",
            "host": "test",
        },
        user=users_models.DatabaseUser(
            name="test", idp_identifier="test", role=users_models.Role.USER
        ),
        connection_method=tools_models.GuacamoleConnectionMethod(),
    )

    assert response["config"]


@responses.activate
@pytest.mark.usefixtures("guacamole_create_token")
def test_validate_guacamole():
    assert guacamole.GuacamoleIntegration.validate_guacamole() is True


@responses.activate
@pytest.mark.parametrize("guacamole_create_token", [500], indirect=True)
@pytest.mark.usefixtures("guacamole_create_token")
def test_validate_guacamole_error():
    assert guacamole.GuacamoleIntegration.validate_guacamole() is False
