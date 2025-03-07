# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging

import pytest
import responses
from aioresponses import aioresponses
from sqlalchemy import orm

import capellacollab.settings.modelsources.git.crud as git_crud
import capellacollab.settings.modelsources.git.models as git_models
import capellacollab.settings.modelsources.t4c.instance.models as t4c_models
import capellacollab.settings.modelsources.t4c.instance.repositories.interface as t4c_repositories_interface
from capellacollab.core import credentials


@pytest.fixture(name="mock_git_valkey_cache")
def fixture_mock_git_valkey_cache(monkeypatch: pytest.MonkeyPatch):
    class MockGitValkeyCache:
        cache: dict[str, tuple[datetime.datetime, bytes]] = {}

        def __init__(self, *args, **kwargs) -> None:
            super().__init__()

        def get_file_data(
            self,
            file_path: str,
            revision: str,
            logger: logging.LoggerAdapter,
        ) -> tuple[datetime.datetime, bytes] | None:
            return MockGitValkeyCache.cache.get(f"f:{file_path}", None)

        def get_artifact_data(
            self,
            job_id: str,
            file_path: str,
            logger: logging.LoggerAdapter,
        ) -> tuple[datetime.datetime, bytes] | None:
            return MockGitValkeyCache.cache.get(f"a:{file_path}:{job_id}")

        def put_file_data(
            self,
            file_path: str,
            last_updated: datetime.datetime,
            content: bytes,
            revision: str,
            logger: logging.LoggerAdapter,
        ) -> None:
            MockGitValkeyCache.cache[f"f:{file_path}"] = (
                last_updated,
                content,
            )

        def put_artifact_data(
            self,
            job_id: str,
            file_path: str,
            started_at: datetime.datetime,
            content: bytes,
            logger: logging.LoggerAdapter,
        ) -> None:
            MockGitValkeyCache.cache[f"a:{file_path}:{job_id}"] = (
                started_at,
                content,
            )

        def clear(self) -> None:
            MockGitValkeyCache.cache.clear()

    monkeypatch.setattr(
        "capellacollab.projects.toolmodels.modelsources.git.handler.cache.GitValkeyCache",
        MockGitValkeyCache,
    )

    return MockGitValkeyCache()


@pytest.fixture(name="git_type", params=[git_models.GitType.GITLAB])
def fixture_git_type(request: pytest.FixtureRequest) -> git_models.GitType:
    return request.param


@pytest.fixture(name="git_response_status", params=[200])
def fixture_git_response_status(request: pytest.FixtureRequest) -> int:
    return request.param


@pytest.fixture(
    name="git_instance_api_url", params=["https://example.com/api/v4"]
)
def fixture_git_instance_api_url(
    request: pytest.FixtureRequest,
) -> str:
    return request.param


@pytest.fixture(name="git_instance")
def fixture_git_instance(
    db: orm.Session, git_type: git_models.GitType, git_instance_api_url: str
) -> git_models.DatabaseGitInstance:
    git_instance = git_models.PostGitInstance(
        name="test",
        url="https://example.com/test/project",
        api_url=git_instance_api_url,
        type=git_type,
    )
    return git_crud.create_git_instance(db, git_instance)


@pytest.fixture(name="job_status", params=["success"])
def fixture_job_status(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture(name="job_name", params=["update_capella_diagram_cache"])
def fixture_job_name(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture(name="pipeline_ids")
def fixture_pipeline_ids(
    request: pytest.FixtureRequest,
) -> list[str]:
    if hasattr(request, "param"):
        return request.param
    return ["12345", "12346"]


@pytest.fixture(name="mock_git_rest_api_for_artifacts")
def fixture_mock_git_rest_api_for_artifacts(
    job_status: str,
    git_type: git_models.GitType,
    job_name: str,
    pipeline_ids: list[str],
):
    match git_type:
        case git_models.GitType.GITLAB:
            with aioresponses() as mocked:
                mocked.get(
                    "https://example.com/api/v4/projects/test%2Fproject",
                    status=200,
                    payload={"id": "10000"},
                )

                mocked.get(
                    "https://example.com/api/v4/projects/10000/pipelines?ref=main&per_page=20",
                    status=200,
                    payload=[{"id": _id} for _id in pipeline_ids],
                )

                for _id in pipeline_ids:
                    mocked.get(
                        f"https://example.com/api/v4/projects/10000/pipelines/{_id}/jobs",
                        status=200,
                        payload=[
                            {
                                "name": "test",
                                "status": "failure",
                                "started_at": "2023-02-04T02:55:17.788000+00:00",
                                "id": "00001",
                            },
                            {
                                "name": job_name,
                                "status": job_status,
                                "started_at": "2023-02-04T02:55:17.788000+00:00",
                                "id": "00002",
                            },
                        ],
                    )

                yield mocked
        case git_models.GitType.GITHUB:
            artifact_id = 12347
            responses.get(
                "https://example.com/api/v4/repos/test/project/actions/runs?branch=main&per_page=20",
                status=200,
                json={
                    "workflow_runs": [
                        {
                            "id": _id,
                            "name": job_name,
                            "conclusion": job_status,
                            "created_at": "2050-07-23T09:30:47Z",
                        }
                        for _id in pipeline_ids
                    ],
                },
            )
            if pipeline_ids:
                responses.get(
                    f"https://example.com/api/v4/repos/test/project/actions/runs/{pipeline_ids[0]}/artifacts",
                    status=200,
                    json={
                        "artifacts": [{"id": artifact_id, "expired": "false"}]
                    },
                )
            yield responses


@pytest.fixture(name="git_query_params")
def fixture_git_query_params(request: pytest.FixtureRequest) -> list[dict]:
    return request.param


@pytest.fixture(name="mock_git_get_commit_information_api")
def fixture_mock_git_get_commit_information_api(
    request: pytest.FixtureRequest,
    git_type: git_models.GitType,
    git_response_status: int,
    git_query_params: list[dict],
):
    match git_type:
        case git_models.GitType.GITLAB:
            for params in git_query_params:
                responses.get(
                    "https://example.com/api/v4/projects/10000/repository/commits",
                    status=git_response_status,
                    json=[
                        {
                            "id": "ee85bc253111b7a8ca2ce5aa26b8f5f36325f48a",
                            "created_at": "2050-04-11T10:09:59.000+02:00",
                            "title": "test: Test commit message",
                            "message": "test: Test commit message\n",
                            "author_name": "test-name",
                            "author_email": "test-email",
                            "authored_date": "2050-04-11T10:09:59.000+02:00",
                            "committer_name": "test-name",
                            "committer_email": "test-email",
                            "committed_date": "2050-04-11T10:09:59.000+02:00",
                        }
                    ],
                    match=[responses.matchers.query_param_matcher(params)],
                )
        case git_models.GitType.GITHUB:
            for params in git_query_params:
                responses.get(
                    "https://example.com/api/v4/repos/test/project/commits",
                    status=git_response_status,
                    json=[
                        {
                            "sha": "43bf21488c5cc309af0ec635a8698b8509379527",
                            "commit": {
                                "author": {
                                    "name": "test-name",
                                    "email": "test-email",
                                    "date": "2050-06-26T13:46:21Z",
                                },
                                "committer": {
                                    "name": "test-name",
                                    "email": "test-email",
                                    "date": "2050-07-03T09:50:57Z",
                                },
                                "message": "test: Test commit message",
                            },
                        }
                    ],
                    match=[responses.matchers.query_param_matcher(params)],
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
