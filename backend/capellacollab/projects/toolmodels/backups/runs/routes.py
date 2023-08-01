# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import base64
import datetime

import fastapi
import fastapi_pagination
from sqlalchemy import orm

from capellacollab.core import database
from capellacollab.core.authentication import injectables as auth_injectables
from capellacollab.core.logging import loki
from capellacollab.projects.users import models as projects_users_models
from capellacollab.users import injectables as user_injectables
from capellacollab.users import models as user_models

from .. import injectables as pipeline_injectables
from .. import models as pipeline_models
from . import crud, helper, injectables, interface, models

router = fastapi.APIRouter(
    dependencies=[
        fastapi.Depends(
            auth_injectables.ProjectRoleVerification(
                required_role=projects_users_models.ProjectUserRole.MANAGER
            )
        )
    ]
)


@router.post(
    "",
    status_code=200,
    response_model=models.PipelineRun,
)
def create_pipeline_run(
    body: models.BackupPipelineRun,
    pipeline: pipeline_models.DatabaseBackup = fastapi.Depends(
        pipeline_injectables.get_existing_pipeline
    ),
    triggerer: user_models.DatabaseUser = fastapi.Depends(
        user_injectables.get_own_user
    ),
    db: orm.Session = fastapi.Depends(database.get_db),
) -> models.DatabasePipelineRun:
    environment = {}
    if body.include_commit_history:
        environment["INCLUDE_COMMIT_HISTORY"] = "true"

    return crud.create_pipeline_run(
        db,
        models.DatabasePipelineRun(
            status=models.PipelineRunStatus.PENDING,
            pipeline=pipeline,
            triggerer=triggerer,
            trigger_time=datetime.datetime.now(),
            environment=environment,
        ),
    )


@router.get(
    "",
    status_code=200,
)
def get_pipeline_runs(
    db: orm.Session = fastapi.Depends(database.get_db),
    pipeline: pipeline_models.DatabaseBackup = fastapi.Depends(
        pipeline_injectables.get_existing_pipeline
    ),
) -> fastapi_pagination.Page[models.PipelineRun]:
    return crud.get_pipeline_runs_for_pipeline_id_paginated(db, pipeline)


@router.get(
    "/{pipeline_run_id}",
    status_code=200,
    response_model=models.PipelineRun,
)
def get_pipeline_run(
    pipeline_run: models.DatabasePipelineRun = fastapi.Depends(
        injectables.get_existing_pipeline_run
    ),
) -> models.DatabasePipelineRun:
    return pipeline_run


@router.get(
    "/{pipeline_run_id}/events",
    response_model=str,
)
def get_events(
    pipeline_run: models.DatabasePipelineRun = fastapi.Depends(
        injectables.get_existing_pipeline_run
    ),
):
    event_logs = loki.fetch_logs_from_loki(
        query=f'{{pipeline_run_id="{pipeline_run.id}", job_name="{pipeline_run.reference_id}", log_type="events"}}',
        start_time=pipeline_run.trigger_time,
        end_time=_determine_end_time_from_pipeline_run(pipeline_run),
    )
    if not event_logs:
        return ""

    return "\n".join(
        [
            _transform_unix_nanoseconds_to_human_readable_format(
                int(logline[0])
            )
            + ": "
            + logline[1]
            for logentry in event_logs
            for logline in logentry["values"]
        ]
    )


def _determine_end_time_from_pipeline_run(
    pipeline_run: models.DatabasePipelineRun,
) -> datetime.datetime:
    max_pipeline_run_duration = datetime.timedelta(
        minutes=interface.PIPELINES_TIMEOUT + 5
    )  # Add 5 minutes tolerance to pipeline timeout
    return min(
        pipeline_run.trigger_time + max_pipeline_run_duration,
        pipeline_run.end_time or datetime.datetime.now(),
    )


def _transform_unix_nanoseconds_to_human_readable_format(
    nanoseonds: int,
) -> str:
    return datetime.datetime.fromtimestamp(int(nanoseonds) / 10**9).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


@router.get("/{pipeline_run_id}/logs", response_model=str)
def get_logs(
    pipeline_run: models.DatabasePipelineRun = fastapi.Depends(
        injectables.get_existing_pipeline_run
    ),
):
    logs = loki.fetch_logs_from_loki(
        query=f'{{pipeline_run_id="{pipeline_run.id}", job_name="{pipeline_run.reference_id}", log_type="logs"}}',
        start_time=pipeline_run.trigger_time,
        end_time=_determine_end_time_from_pipeline_run(pipeline_run),
    )
    if not logs:
        return ""

    logs = "\n".join(
        [
            datetime.datetime.fromtimestamp(
                int(logline[0]) / 10**9
            ).strftime("%Y-%m-%d %H:%M:%S")
            + ": "
            + logline[1]
            for logentry in logs
            for logline in logentry["values"]
        ]
    )

    masked_values = [
        pipeline_run.pipeline.t4c_password,
        pipeline_run.pipeline.t4c_model.repository.instance.password,
    ]
    masked_values_generated = []

    # Also mask derivated, e.g. base64 encoded credentials
    for value in masked_values:
        masked_values_generated.append(
            base64.b64encode(value.encode("utf-8")).decode("utf-8")
        )

    return helper.filter_logs(logs, masked_values + masked_values_generated)


fastapi_pagination.add_pagination(router)
