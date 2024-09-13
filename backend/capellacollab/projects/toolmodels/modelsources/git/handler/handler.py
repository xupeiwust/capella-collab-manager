# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import abc
import datetime

from . import cache


class GitHandler:
    def __init__(
        self,
        git_model_id: int,
        path: str,
        revision: str,
        password: str,
        api_url: str,
        repository_id: str,
    ) -> None:
        self.path = path
        self.revision = revision
        self.password = password
        self.api_url = api_url
        self.repository_id = repository_id
        self.cache = cache.GitValkeyCache(git_model_id)

    @classmethod
    @abc.abstractmethod
    async def get_repository_id_by_git_url(
        cls, path: str, password: str, api_url: str
    ) -> str:
        pass

    @abc.abstractmethod
    async def get_last_successful_job_run(
        self, job_name: str
    ) -> tuple[str, datetime.datetime]:
        """
        Retrieve the ID and start time of the most recent run for a specified job.

        Args:
            job_name (str): The name of the job whose last run information is to be retrieved.

        Returns:
            tuple[str, datetime.datetime]: A tuple containing the job ID and the start time (as a datetime object) of the most recent run.

        Raises:
            GitPipelineJobNotFoundError: If the job cannot be found in any of the recent pipeline runs.
            GitPipelineJobUnsuccessfulError: If the last job state indicates that the job was not successful.
        """

    @abc.abstractmethod
    def get_artifact_from_job(
        self, job_id: str | int, trusted_path_to_artifact: str
    ) -> bytes:
        """
        Retrieve an artifact from a specified job.

        Args:
            job_id (str): The unique identifier of the job from which to retrieve the artifact.
            trusted_path_to_artifact (str): The path within the job's artifacts where the desired artifact is stored.

        Returns:
            bytes: The content of the artifact as a byte stream.
        """

    @abc.abstractmethod
    def get_file_from_repository(
        self, trusted_file_path: str, revision: str | None = None
    ) -> bytes:
        """
        Retrieve the contents of a specified file from the repository.

        Args:
            trusted_file_path (str): The path to the file within the repository.
            revision (str | None): The specific revision to use. If None, the handler revision is used.

        Returns:
            bytes: The content of the file.

        Raises:
            GitRepositoryFileNotFoundError: If the file does not exist in the specified revision.
        """

    @abc.abstractmethod
    def get_last_updated_for_file(
        self, file_path: str, revision: str | None = None
    ) -> datetime.datetime:
        """
        Retrieve the last update datetime for the specified file in the repository.

        Args:
            file_path (str): The path to the file within the repository.
            revision (str | None): The specific revision to use. If None, the handler revision is used.

        Returns:
            datetime.datetime: The datetime of the last update to the specified file.

        Raises:
            GitRepositoryFileNotFoundError: If the file does not exist in the revision.
        """

    @abc.abstractmethod
    def get_started_at_for_job(self, job_id: str | int) -> datetime.datetime:
        """
        Retrieve the start datetime for the specified job in the repository.

        Args:
            job_id (str): The unique identifier of the job from which to retrieve the artifact.

        Returns:
            datetime.datetime: The datetime of the start time of the specified job.
        """

    async def get_file(
        self, trusted_file_path: str, revision: str
    ) -> tuple[datetime.datetime, bytes]:
        last_updated = self.get_last_updated_for_file(
            trusted_file_path, revision
        )

        if file_data := self.cache.get_file_data(trusted_file_path, revision):
            last_updated_cache, content_cache = file_data

            if last_updated == last_updated_cache:
                return last_updated_cache, content_cache

        content = self.get_file_from_repository(trusted_file_path, revision)
        self.cache.put_file_data(
            trusted_file_path, last_updated, content, revision
        )

        return last_updated, content

    async def get_artifact(
        self,
        trusted_file_path: str,
        job_name: str,
        job_id: str | int | None = None,
    ) -> tuple[str | int, datetime.datetime, bytes]:
        if not job_id:
            job_id, started_at = await self.get_last_successful_job_run(
                job_name
            )
        else:
            started_at = self.get_started_at_for_job(job_id)

        if artifact_data := self.cache.get_artifact_data(
            job_id, trusted_file_path
        ):
            return job_id, artifact_data[0], artifact_data[1]

        content = self.get_artifact_from_job(job_id, trusted_file_path)
        self.cache.put_artifact_data(
            job_id, trusted_file_path, started_at, content
        )

        return job_id, started_at, content
