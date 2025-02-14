# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import binascii
import http
import json
import logging
import random
import shlex
import string
import subprocess
import typing as t

import kubernetes
import kubernetes.config
import kubernetes.stream.stream
import prometheus_client
import yaml
from kubernetes import client
from kubernetes.client import exceptions
from openshift import dynamic
from openshift.dynamic import exceptions as dynamic_exceptions

from capellacollab.config import config

from . import helper, models

log = logging.getLogger(__name__)

SESSIONS_STARTED = prometheus_client.Counter(
    "backend_sessions_started", "", ("session_type",)
)
SESSIONS_KILLED = prometheus_client.Counter(
    "backend_sessions_killed", "Sessions killed, either by user or timeout"
)

external_registry: str = config["docker"]["externalRegistry"]

cfg: dict[str, t.Any] = config["k8s"]

namespace: str = cfg["namespace"]
storage_access_mode: str = cfg["storageAccessMode"]
storage_class_name: str = cfg["storageClassName"]

loki_enabled: bool = cfg["promtail"]["lokiEnabled"]


def deserialize_kubernetes_resource(content: t.Any, resource: str):
    # This is needed as "workaround" for the deserialize function
    class FakeKubeResponse:
        def __init__(self, obj):
            self.data = json.dumps(obj)

    return client.ApiClient().deserialize(FakeKubeResponse(content), resource)


# Resolve securityContext and pullPolicy
image_pull_policy: str = cfg.get("cluster", {}).get(
    "imagePullPolicy", "Always"
)

pod_security_context = None
if _pod_security_context := cfg.get("cluster", {}).get(
    "podSecurityContext", None
):
    pod_security_context = deserialize_kubernetes_resource(
        _pod_security_context, client.V1PodSecurityContext.__name__
    )


def is_openshift_cluster(api_client):
    dyn_client = dynamic.DynamicClient(api_client)
    try:
        dyn_client.resources.get(
            api_version="route.openshift.io/v1", kind="Route"
        )
        logging.info(
            "Openshift routes detected, assuming an OpenShift cluster"
        )
        return True
    except dynamic_exceptions.ResourceNotFoundError:
        logging.info(
            "No openshift routes detected, assuming normal Kubernetes cluster"
        )
        return False


class KubernetesOperator:
    def __init__(self) -> None:
        self.load_config()
        self.client = client.ApiClient()
        self.v1_core = client.CoreV1Api(api_client=self.client)
        self.v1_apps = client.AppsV1Api(api_client=self.client)
        self.v1_batch = client.BatchV1Api(api_client=self.client)
        self.v1_networking = client.NetworkingV1Api(api_client=self.client)
        self.v1_policy = client.PolicyV1Api(api_client=self.client)
        self._openshift = None

    @property
    def openshift(self):
        if self._openshift is None:
            self._openshift = is_openshift_cluster(self.client)
        return self._openshift

    def load_config(self) -> None:
        self.kubectl_arguments = []
        if cfg.get("context", None):
            self.kubectl_arguments += ["--context", cfg["context"]]
            kubernetes.config.load_config(context=cfg["context"])
        else:
            kubernetes.config.load_incluster_config()

    def validate(self) -> bool:
        try:
            self.v1_core.get_api_resources()
            return True
        except BaseException:
            return False

    def create_public_route(
        self,
        session_id: str,
        host: str,
        path: str,
        port: int,
        wildcard_host: bool | None = False,
    ):
        """Create a public route for the session

        Parameters
        ==========
        session_id: str
            The database ID of the session
        host: str
            The host to use for the route
        path: str
            The path to use for the route
        port: int
            The port to use for the route
        wildcard_host: bool
            Whether to use a wildcard host or not (serve on all hosts),
            not supported for OpenShift
        """
        if self.openshift:
            self._create_openshift_route(session_id, host, path, port)
        else:
            self._create_ingress(session_id, host, path, port, wildcard_host)

    def delete_public_route(self, session_id: str):
        if self.openshift:
            if dep_status := self._delete_openshift_route(session_id):
                log.info(
                    "Deleted route %s with status %s",
                    session_id,
                    dep_status.status,
                )
        else:
            if dep_status := self._delete_ingress(session_id):
                log.info(
                    "Deleted ingress %s with status %s",
                    session_id,
                    dep_status.status,
                )

    def start_session(
        self,
        image: str,
        username: str,
        session_type: str,
        tool_name: str,
        version_name: str,
        environment: dict[str, str],
        ports: dict[str, int],
        volumes: list[models.Volume],
        prometheus_path="/metrics",
        prometheus_port=9118,
        limits="high",
    ) -> dict[str, t.Any]:
        log.info("Launching a %s session for user %s", session_type, username)

        _id = self._generate_id()

        if loki_enabled:
            self._create_promtail_configmap(
                name=_id,
                username=username,
                session_type=session_type,
                tool_name=tool_name,
                version_name=version_name,
            )

        deployment = self._create_deployment(
            image=image,
            name=_id,
            environment=environment,
            ports=ports,
            volumes=volumes,
            limits=limits,
        )

        self._create_disruption_budget(
            name=_id,
            deployment_name=_id,
        )

        service = self._create_service(
            name=_id,
            deployment_name=_id,
            ports=ports,
            prometheus_path=prometheus_path,
            prometheus_port=prometheus_port,
        )

        log.info(
            "Launched a %s session for user %s with id %s",
            session_type,
            username,
            _id,
        )
        SESSIONS_STARTED.labels(session_type).inc()

        return self._export_attrs(deployment, service, ports)

    def kill_session(self, _id: str):
        log.info("Terminating session %s", _id)

        if dep_status := self._delete_deployment(name=_id):
            log.info(
                "Deleted deployment %s with status %s", _id, dep_status.status
            )

        if disrupt_status := self._delete_disruptionbudget(name=_id):
            log.info(
                "Deleted Pod discruption budget %s with status %s",
                _id,
                disrupt_status.status,
            )

        if loki_enabled and (conf_status := self._delete_config_map(name=_id)):
            log.info(
                "Deleted config map %s with status %s", _id, conf_status.status
            )

        if svc_status := self._delete_service(name=_id):
            log.info(
                "Deleted service %s with status %s", _id, svc_status.status
            )

        SESSIONS_KILLED.inc()

    def get_job_by_name(self, name: str) -> client.V1Job:
        return self.v1_batch.read_namespaced_job(name, namespace=namespace)

    def get_session_state(self, _id: str) -> str:
        return self._get_pod_state(label_selector=f"app={_id}")

    def _get_pod_state(self, label_selector: str):
        try:
            pod = self.get_pods(label_selector=label_selector)[0]
            pod_name = pod.metadata.name

            log.debug("Received k8s pod: %s", pod_name)
            log.debug("Fetching k8s events for pod: %s", pod_name)

            events: list[
                client.CoreV1Event
            ] = self.v1_core.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}",
            ).items

            events = list(filter(self._is_non_promtail_event, events))
            if events:
                return events[-1].reason

            # Fallback if no event is available
            return pod.status.phase

        except exceptions.ApiException as e:
            log.warning("Kubernetes error", exc_info=True)
            return f"error-{str(e.status)}"
        except Exception:
            log.exception("Error getting the session state")

        return "unknown"

    def _is_non_promtail_event(self, event: client.CoreV1Event) -> bool:
        if not (event.involved_object and event.involved_object.field_path):
            return True

        return "spec.containers{promtail}" != event.involved_object.field_path

    def get_session_logs(self, _id: str) -> str:
        return self.v1_core.read_namespaced_pod_log(
            name=self._get_pod_name(_id),
            container=_id,
            namespace=namespace,
        )

    def get_job_logs(self, name: str) -> str | None:
        pod_name = self.get_pod_name_from_job_name(name)
        try:
            if pod_log := self.v1_core.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                pretty=True,
                timestamps=True,
            ):
                return pod_log
        except Exception:
            log.exception(
                "Failed fetching logs from Kubernetes", exc_info=True
            )
        return None

    def get_events_for_involved_object(
        self, name: str
    ) -> list[client.CoreV1Event]:
        return self.v1_core.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={name}",
        ).items

    def create_cronjob(
        self,
        image: str,
        command: str,
        environment: dict[str, str | None],
        schedule="* * * * *",
        timeout=18000,
    ) -> str:
        _id = self._generate_id()
        self._create_cronjob(
            name=_id,
            image=image,
            job_labels={
                "workload": "cronjob",
                "app.capellacollab/parent": _id,
            },
            environment=environment,
            args=[command],
            schedule=schedule,
            timeout=timeout,
        )
        return _id

    def create_job(
        self,
        image: str,
        command: str,
        labels: dict[str, str],
        environment: dict[str, str | None],
        timeout: int = 18000,
    ) -> str:
        _id = self._generate_id()
        self._create_job(
            name=_id,
            image=image,
            job_labels={"workload": "job", **labels},
            environment=environment,
            args=[command],
            timeout=timeout,
        )
        return _id

    def delete_cronjob(self, _id: str):
        try:
            self.v1_batch.delete_namespaced_cron_job(
                namespace=namespace, name=_id
            )
        except exceptions.ApiException:
            log.exception("Error deleting cronjob with name: %s", _id)

    def delete_job(self, name: str):
        log.info("Deleting job '%s' in cluster", name)
        try:
            self.v1_batch.delete_namespaced_job(
                namespace=namespace, name=name, propagation_policy="Background"
            )
        except exceptions.ApiException:
            log.error("Error deleting job with name: %s", name)

    def get_pod_name_from_job_name(self, job_name: str) -> str | None:
        return self._get_pod_id(label_selector=f"job-name={job_name}")

    def get_pod_for_job(self, job_name: str) -> client.V1Pod:
        pods = self.v1_core.list_namespaced_pod(
            namespace=namespace, label_selector=f"job-name={job_name}"
        )
        if len(pods.items) == 1:
            return pods.items[0]
        return None

    def _get_pod_id(self, label_selector: str) -> str:
        try:
            pods = self.v1_core.list_namespaced_pod(
                namespace=namespace, label_selector=label_selector
            ).to_dict()

            return pods["items"][0]["metadata"]["name"]
        except Exception:
            log.exception("Error fetching the Pod ID")
            return ""

    def _generate_id(self) -> str:
        return "".join(random.choices(string.ascii_lowercase, k=25))

    def _export_attrs(
        self,
        deployment: client.V1Deployment,
        service: client.V1Service,
        ports: dict[str, int],
    ) -> dict[str, t.Any]:
        if "rdp" in ports:
            port = {ports["rdp"]}
        elif "http" in ports:
            port = {ports["http"]}
        else:
            raise ValueError(
                "No rdp or http port defined on the deployed session"
            )

        return {
            "id": deployment.to_dict()["metadata"]["name"],
            "ports": port,
            "created_at": deployment.to_dict()["metadata"][
                "creation_timestamp"
            ],
            "host": service.to_dict()["metadata"]["name"] + "." + namespace,
        }

    def _map_volumes_to_k8s_volumes(
        self,
        volumes: list[models.Volume],
    ) -> tuple[list[client.V1Volume], list[client.V1VolumeMount]]:
        k8s_volumes: list[client.V1Volume] = []
        k8s_volume_mounts: list[client.V1VolumeMount] = []

        for volume in volumes:
            k8s_volumes.append(self._map_volume_to_k8s_volume(volume))

            k8s_volume_mounts.append(
                client.V1VolumeMount(
                    name=volume.name,
                    mount_path=str(volume.container_path),
                    read_only=volume.read_only,
                )
            )

        return k8s_volumes, k8s_volume_mounts

    def _map_volume_to_k8s_volume(self, volume: models.Volume):
        if isinstance(volume, models.PersistentVolume):
            return client.V1Volume(
                name=volume.name,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=volume.volume_name
                ),
            )

        if isinstance(volume, models.EmptyVolume):
            return client.V1Volume(
                name=volume.name,
                empty_dir=client.V1EmptyDirVolumeSource(),
            )

        raise KeyError(
            f"The Kubernetes operator encountered an unsupported session volume type '{type(volume)}'"
        )

    def _create_deployment(
        self,
        image: str,
        name: str,
        environment: dict[str, str],
        ports: dict[str, int],
        volumes: list[models.Volume],
        limits: str = "high",
    ) -> client.V1Deployment:
        k8s_volumes, k8s_volume_mounts = self._map_volumes_to_k8s_volumes(
            volumes
        )
        promtail_volume_mounts: list[client.V1VolumeMount] = []

        if loki_enabled:
            promtail_volume_mounts.append(
                client.V1VolumeMount(
                    name="workspace", mount_path="/var/log/promtail"
                )
            )

            k8s_volumes.append(
                client.V1Volume(
                    name="prom-config",
                    config_map=client.V1ConfigMapVolumeSource(name=name),
                )
            )

            promtail_volume_mounts.append(
                client.V1VolumeMount(
                    name="prom-config", mount_path="/etc/promtail"
                )
            )

        # TODO: This should be moved to a configuration hook once it supports volumes. # pylint: disable=fixme
        if pure_variants_secret_name := environment.get(
            "PURE_VARIANTS_SECRET"
        ):
            k8s_volume_mounts.append(
                client.V1VolumeMount(
                    name="pure-variants",
                    mount_path="/inputs/pure-variants",
                    read_only=True,
                )
            )

            k8s_volumes.append(
                client.V1Volume(
                    name="pure-variants",
                    secret=client.V1SecretVolumeSource(
                        secret_name=pure_variants_secret_name, optional=True
                    ),
                )
            )

        resources = (
            client.V1ResourceRequirements(
                limits={"cpu": "2", "memory": "3Gi"},
                requests={"cpu": "1", "memory": "500Mi"},
            )
            if limits == "low"
            else client.V1ResourceRequirements(
                limits={"cpu": "2", "memory": "6Gi"},
                requests={"cpu": "0.4", "memory": "1.6Gi"},
            )
        )

        containers: list[client.V1Container] = []
        containers.append(
            client.V1Container(
                name=name,
                image=image,
                ports=[
                    client.V1ContainerPort(container_port=port, protocol="TCP")
                    for port in ports.values()
                ],
                env=[
                    client.V1EnvVar(name=key, value=str(value))
                    for key, value in environment.items()
                ],
                resources=resources,
                volume_mounts=k8s_volume_mounts,
                image_pull_policy=image_pull_policy,
            )
        )
        if loki_enabled:
            containers.append(
                client.V1Container(
                    name="promtail",
                    image=f"{external_registry}/grafana/promtail",
                    args=[
                        "--config.file=/etc/promtail/promtail.yaml",
                        "-log-config-reverse-order",
                    ],
                    ports=[
                        client.V1ContainerPort(
                            name="metrics", container_port=3101, protocol="TCP"
                        )
                    ],
                    resources=client.V1ResourceRequirements(
                        limits={"cpu": "0.1", "memory": "50Mi"},
                        requests={"cpu": "0.05", "memory": "5Mi"},
                    ),
                    volume_mounts=promtail_volume_mounts,
                    image_pull_policy=image_pull_policy,
                )
            )

        deployment: client.V1Deployment = client.V1Deployment(
            kind="Deployment",
            api_version="apps/v1",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                strategy=client.V1DeploymentStrategy(type="Recreate"),
                selector=client.V1LabelSelector(match_labels={"app": name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": name, "workload": "session"}
                    ),
                    spec=client.V1PodSpec(
                        security_context=pod_security_context,
                        containers=containers,
                        volumes=k8s_volumes,
                        restart_policy="Always",
                    ),
                ),
            ),
        )

        return self.v1_apps.create_namespaced_deployment(namespace, deployment)

    def create_secret(
        self, name: str, content: dict[str, bytes], overwrite: bool = False
    ) -> client.V1Secret:
        content_b64 = {
            key: base64.b64encode(value).decode()
            for key, value in content.items()
        }

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            data=content_b64,
        )

        if overwrite:
            self.delete_secret(name)
        return self.v1_core.create_namespaced_secret(cfg["namespace"], secret)

    def _create_cronjob(
        self,
        name: str,
        image: str,
        job_labels: dict[str, str],
        environment: dict[str, str | None],
        args: list[str] | None = None,
        schedule: str = "* * * * *",
        timeout: int = 18000,
    ) -> client.V1CronJob:
        cron_job: client.V1CronJob = client.V1CronJob(
            kind="CronJob",
            api_version="batch/v1",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1CronJobSpec(
                schedule=schedule,
                job_template=client.V1JobTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=job_labels),
                    spec=self._create_job_spec(
                        name=name,
                        image=image,
                        job_labels=job_labels,
                        environment=environment,
                        args=args,
                        timeout=timeout,
                    ),
                ),
            ),
        )
        return self.v1_batch.create_namespaced_cron_job(namespace, cron_job)

    def _create_job(
        self,
        name: str,
        image: str,
        job_labels: dict[str, str],
        environment: dict[str, str | None],
        args: list[str] | None = None,
        timeout=18000,
    ) -> client.V1Job:
        job: client.V1Job = client.V1Job(
            kind="Job",
            api_version="batch/v1",
            metadata=client.V1ObjectMeta(name=name),
            spec=self._create_job_spec(
                name=name,
                image=image,
                job_labels=job_labels,
                environment=environment,
                args=args,
                timeout=timeout,
            ),
        )
        return self.v1_batch.create_namespaced_job(namespace, job)

    def _create_disruption_budget(
        self,
        name: str,
        deployment_name: str,
    ) -> client.V1PodDisruptionBudget:
        """Disallow any pod discription for the deployment

        If the deployment uses the recreate strategy together with
        this budget, the cluster operator shall consult the administrator before
        termination of the deployment.

        More information:
        https://kubernetes.io/docs/tasks/run-application/configure-pdb/
        """

        discruption_budget: client.V1PodDisruptionBudget = (
            client.V1PodDisruptionBudget(
                kind="PodDisruptionBudget",
                api_version="policy/v1",
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels={"app": name},
                ),
                spec=client.V1PodDisruptionBudgetSpec(
                    max_unavailable=0,
                    selector=client.V1LabelSelector(
                        match_labels={"app": deployment_name}
                    ),
                ),
            )
        )
        return self.v1_policy.create_namespaced_pod_disruption_budget(
            namespace, discruption_budget
        )

    def _create_service(
        self,
        name: str,
        deployment_name: str,
        ports: dict[str, int],
        prometheus_path: str,
        prometheus_port: int,
    ) -> client.V1Service:
        service: client.V1Service = client.V1Service(
            kind="Service",
            api_version="v1",
            metadata=client.V1ObjectMeta(
                name=name,
                labels={"app": name},
                annotations={
                    "prometheus.io/scrape": "true",
                    "prometheus.io/path": prometheus_path,
                    "prometheus.io/port": f"{prometheus_port}",
                },
            ),
            spec=client.V1ServiceSpec(
                ports=[
                    client.V1ServicePort(
                        name=name,
                        protocol="TCP",
                        port=port,
                        target_port=port,
                    )
                    for name, port in ports.items()
                ],
                selector={"app": deployment_name},
                type="ClusterIP",
            ),
        )
        return self.v1_core.create_namespaced_service(namespace, service)

    def _create_ingress(
        self,
        id,
        host: str,
        path: str,
        port_number: int,
        wildcard_host: bool | None = False,
    ):
        ingress = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=id,
            ),
            spec=client.V1IngressSpec(
                ingress_class_name=cfg.get("ingressClassName"),
                rules=[
                    client.V1IngressRule(
                        host=None if wildcard_host else host,
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path=path,
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=id,
                                            port=client.V1ServiceBackendPort(
                                                number=port_number
                                            ),
                                        )
                                    ),
                                )
                            ]
                        ),
                    )
                ],
            ),
        )
        return self.v1_networking.create_namespaced_ingress(namespace, ingress)

    def _create_openshift_route(
        self, id, host: str, path: str, port_number: int
    ):
        route_dict = {
            "kind": "Route",
            "apiVersion": "route.openshift.io/v1",
            "metadata": {
                "name": id,
            },
            "spec": {
                "host": host,
                "path": path,
                "to": {
                    "kind": "Service",
                    "name": id,
                },
                "port": {
                    "targetPort": port_number,
                },
                "tls": {
                    "termination": "edge",
                    "insecureEdgeTerminationPolicy": "Redirect",
                },
                "wildcardPolicy": "None",
            },
        }
        dyn_client = dynamic.DynamicClient(self.client)
        v1_routes = dyn_client.resources.get(
            api_version="route.openshift.io/v1", kind="Route"
        )
        return v1_routes.create(body=route_dict, namespace=namespace)

    def create_persistent_volume(
        self, name: str, size: str, labels: dict[str, str] | None = None
    ):
        pvc: client.V1PersistentVolumeClaim = client.V1PersistentVolumeClaim(
            kind="PersistentVolumeClaim",
            api_version="v1",
            metadata=client.V1ObjectMeta(name=name, labels=labels),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=[storage_access_mode],
                storage_class_name=storage_class_name,
                resources=client.V1ResourceRequirements(
                    requests={"storage": size}
                ),
            ),
        )

        try:
            self.v1_core.create_namespaced_persistent_volume_claim(
                namespace, pvc
            )
        except exceptions.ApiException as e:
            # Persistent volume already exists
            if e.status == 409:
                return
            raise

    def delete_persistent_volume(self, name: str):
        try:
            self.v1_core.delete_namespaced_persistent_volume_claim(
                name=name, namespace=namespace
            )
        except exceptions.ApiException as e:
            # Persistent volume doesn't exist or was already deleted
            # Nothing to do
            if e.status == http.HTTPStatus.NOT_FOUND:
                return
            raise

    def _create_job_spec(
        self,
        name: str,
        image: str,
        job_labels: dict[str, str],
        environment: dict[str, str | None],
        args: list[str] | None = None,
        timeout: int = 18000,
    ) -> client.V1JobSpec:
        containers: list[client.V1Container] = [
            client.V1Container(
                name=name,
                image=image,
                args=args,
                env=[
                    client.V1EnvVar(name=key, value=str(value))
                    for key, value in environment.items()
                ],
                resources=client.V1ResourceRequirements(
                    limits={"cpu": "2", "memory": "6Gi"},
                    requests={"cpu": "0.4", "memory": "1.6Gi"},
                ),
                image_pull_policy=image_pull_policy,
            )
        ]
        return client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=job_labels),
                spec=client.V1PodSpec(
                    security_context=pod_security_context,
                    containers=containers,
                    restart_policy="Never",
                ),
            ),
            ttl_seconds_after_finished=3600,  # Keep job for one hour, we'll handle the deletion on our own.
            backoff_limit=0,
            active_deadline_seconds=timeout,
        )

    def _create_promtail_configmap(
        self,
        name: str,
        username: str,
        session_type: str,
        tool_name: str,
        version_name: str,
    ) -> client.V1ConfigMap:
        config_map: client.V1ConfigMap = client.V1ConfigMap(
            kind="ConfigMap",
            api_version="v1",
            metadata=client.V1ObjectMeta(name=name),
            data={
                "promtail.yaml": yaml.dump(
                    {
                        "server": {
                            "http_listen_port": cfg["promtail"]["serverPort"],
                        },
                        "clients": [
                            {
                                "url": cfg["promtail"]["lokiUrl"] + "/push",
                                "basic_auth": {
                                    "username": cfg["promtail"][
                                        "lokiUsername"
                                    ],
                                    "password": cfg["promtail"][
                                        "lokiPassword"
                                    ],
                                },
                            }
                        ],
                        "positions": {
                            "filename": "/var/log/promtail/positions.yaml"
                        },
                        "scrape_configs": [
                            {
                                "job_name": "system",
                                "pipeline_stages": [
                                    {
                                        "multiline": {
                                            "firstline": "^[^\t]",
                                        },
                                    }
                                ],
                                "static_configs": [
                                    {
                                        "targets": ["localhost"],
                                        "labels": {
                                            "deployment": f"{namespace}-sessions",
                                            "username": username,
                                            "session_type": session_type,
                                            "tool": tool_name,
                                            "version": version_name,
                                            "__path__": "/var/log/promtail/**/*.log",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                )
            },
        )
        return self.v1_core.create_namespaced_config_map(namespace, config_map)

    def _delete_deployment(self, name: str) -> client.V1Status | None:
        try:
            return self.v1_apps.delete_namespaced_deployment(name, namespace)
        except exceptions.ApiException:
            log.exception("Error deleting deployment with name: %s", name)
            return None

    def delete_secret(self, name: str) -> kubernetes.client.V1Status | None:
        try:
            return self.v1_core.delete_namespaced_secret(name, namespace)
        except client.exceptions.ApiException:
            log.exception("Error deleting secret with name: %s", name)
            return None

    def _delete_config_map(self, name: str) -> client.V1Status | None:
        try:
            return self.v1_core.delete_namespaced_config_map(name, namespace)
        except exceptions.ApiException:
            log.exception("Error deleting config map with name: %s", name)
            return None

    def _delete_service(self, name: str) -> client.V1Status | None:
        try:
            return self.v1_core.delete_namespaced_service(name, namespace)
        except exceptions.ApiException:
            log.exception("Error deleting service with name: %s", name)
            return None

    def _delete_disruptionbudget(self, name: str) -> client.V1Status | None:
        try:
            return self.v1_policy.delete_namespaced_pod_disruption_budget(
                name, namespace
            )
        except exceptions.ApiException as e:
            # Pod disruption budge doesn't exist or was already deleted
            # Nothing to do
            if not e.status == http.HTTPStatus.NOT_FOUND:
                log.exception(
                    "Error deleting discruptionbudget with name: %s", name
                )

            return None

    def _delete_ingress(self, name: str) -> client.V1Status | None:
        try:
            return self.v1_networking.delete_namespaced_ingress(
                name, namespace
            )
        except exceptions.ApiException:
            log.exception("Error deleting ingress with name: %s", name)
            return None

    def _delete_openshift_route(self, name: str) -> client.V1Status | None:
        try:
            dyn_client = dynamic.DynamicClient(self.client)
            v1_routes = dyn_client.resources.get(
                api_version="route.openshift.io/v1", kind="Route"
            )
            return v1_routes.delete(name=name, namespace=namespace)
        except exceptions.ApiException:
            log.exception("Error deleting route with name: %s", name)
            return None

    def _get_pod_name(self, _id: str) -> str:
        return self.get_pods(label_selector=f"app={_id}")[0].metadata.name

    def get_pods(self, label_selector: str | None) -> list[client.V1Pod]:
        return self.v1_core.list_namespaced_pod(
            namespace=namespace, label_selector=label_selector
        ).items

    def list_files(self, _id: str, directory: str, show_hidden: bool):
        def print_file_tree_as_json():
            import json  # pylint: disable=redefined-outer-name,reimported
            import pathlib
            import sys

            print(  # pylint: disable=bad-builtin
                "Using CLI arguments: " + str(sys.argv[1:]), file=sys.stderr
            )

            def get_files(dir: pathlib.Path, show_hidden: bool):
                file = {
                    "path": str(dir.absolute()),
                    "name": dir.name,
                    "type": "directory",
                    "children": [],
                }

                assert isinstance(file["children"], list)

                for item in dir.iterdir():
                    if not show_hidden and item.name.startswith("."):
                        continue
                    if item.is_dir():
                        file["children"].append(get_files(item, show_hidden))
                    elif item.is_file():
                        file["children"].append(
                            {
                                "name": item.name,
                                "path": str(item.absolute()),
                                "type": "file",
                            }
                        )

                return file

            print(  # pylint: disable=bad-builtin
                json.dumps(
                    get_files(
                        pathlib.Path(sys.argv[1]), json.loads(sys.argv[2])
                    )
                )
            )

        source = helper.get_source_of_python_function(print_file_tree_as_json)

        pod_name = self._get_pod_name(_id)
        # We have to use subprocess to get it running until this issue is solved:
        # https://github.com/kubernetes/kubernetes/issues/89899
        # Python doesn't start evaluating the code before EOF, but there is no way to close stdin

        try:
            response = subprocess.run(
                ["kubectl"]
                + self.kubectl_arguments
                + [
                    "--namespace",
                    namespace,
                    "exec",
                    "--stdin",
                    pod_name,
                    "--container",
                    _id,
                    "--",
                    "python",
                    "-",
                    directory,
                    json.dumps(show_hidden),
                ],
                input=source.encode(),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            log.error(
                "Loading files of session '%s' failed - STDOUT: %s",
                pod_name,
                e.stdout.decode(),
            )
            log.error(
                "Loading files of session '%s' failed - STDERR: %s",
                pod_name,
                e.stderr.decode(),
            )
            raise

        return json.loads(response.stdout)

    def upload_files(
        self,
        _id: str,
        content: bytes,
    ):
        pod_name = self._get_pod_name(_id)

        try:
            exec_command = ["tar", "xf", "-", "-C", "/"]
            stream = kubernetes.stream.stream(
                self.v1_core.connect_get_namespaced_pod_exec,
                pod_name,
                container=_id,
                namespace=namespace,
                command=exec_command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            stream.write_stdin(content)
            stream.update(timeout=5)
            if stream.peek_stdout():
                log.debug(
                    "Upload into %s - STDOUT: %s", _id, stream.read_stdout()
                )
            if stream.peek_stderr():
                log.debug(
                    "Upload into %s - STDERR: %s", _id, stream.read_stderr()
                )

        except exceptions.ApiException:
            log.exception(
                "Exception when copying file to the pod with id %s", _id
            )
            raise

    def download_file(self, _id: str, filename: str) -> t.Iterable[bytes]:
        pod_name = self._get_pod_name(_id)
        try:
            exec_command = [
                "bash",
                "-c",
                f"zip -qr /tmp/archive.zip '{shlex.quote(filename)}' && base64 /tmp/archive.zip && rm -f /tmp/archive.zip",
            ]
            stream = kubernetes.stream.stream(
                self.v1_core.connect_get_namespaced_pod_exec,
                pod_name,
                container=_id,
                namespace=cfg["namespace"],
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            def reader():
                while stream.is_open():
                    content = stream.read_stdout(timeout=60)
                    if content:
                        yield content.encode("utf-8")

            yield from lazy_b64decode(reader())

        except kubernetes.client.exceptions.ApiException:
            log.exception(
                "Exception when copying file to the pod with id %s", _id
            )
            raise


def lazy_b64decode(reader):
    data = b""
    for b64data in reader:
        data += b64data
        try:
            yield base64.b64decode(data)
            data = b""
        except binascii.Error:
            pass
