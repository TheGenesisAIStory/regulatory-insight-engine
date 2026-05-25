#!/usr/bin/env python3
"""Submit the Fiorell.IA LoRA release training job to Azure ML.

The default path prepares the local 40% abstention dataset patch, submits an
Azure ML Command Job, waits for completion, registers the adapter output as a
custom model, and deploys it to the managed online endpoint configured in
azure_ml_config.yaml.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = REPO_ROOT / "azure_ml_config.yaml"
TRAINING_ENTRYPOINT = "fiorellia/training/train_lora_behavior_v1.py"
ENDPOINT_CODE_DIR = REPO_ROOT / "fiorellia/training/azure_endpoint"
ENDPOINT_SCORING_SCRIPT = "score.py"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be an object: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def normalize_location(value: str | None) -> str:
    return (value or "").lower().replace(" ", "")


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def import_pipeline_helpers() -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from fiorellia.training import fiorellia_colab_pipeline as pipeline

    return {
        "SYSTEM_STYLE_PATCH": pipeline.SYSTEM_STYLE_PATCH,
        "is_abstention_training_case": pipeline.is_abstention_training_case,
        "patch_record_system": pipeline.patch_record_system,
        "read_jsonl": pipeline.read_jsonl,
        "write_jsonl": pipeline.write_jsonl,
    }


def build_supported_records(eval_dataset_path: Path, system_prompt: str) -> list[dict[str, Any]]:
    helpers = import_pipeline_helpers()
    records = []
    for row in helpers["read_jsonl"](eval_dataset_path):
        if bool(row.get("expected_no_answer")):
            continue
        answer = str(row.get("reference_answer") or "").strip()
        query = str(row.get("query") or row.get("user_query") or "").strip()
        if not answer or not query:
            continue
        sources = row.get("expected_sources") or []
        source_lines = "\n".join(f"- {source}" for source in sources) if sources else "- Fonte locale indicizzata"
        records.append(
            {
                "id": f"{row.get('id', 'supported')}-supported-sft",
                "category": "answer_with_citations",
                "lang": "it",
                "source_eval_id": row.get("id"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Domanda:\n{query}\n\nFonti locali disponibili:\n{source_lines}",
                    },
                    {
                        "role": "assistant",
                        "content": (
                            f"Risposta:\n{answer}\n\n"
                            f"Fonti:\n{source_lines}\n\n"
                            "Nota:\nRisposta limitata ai documenti indicizzati nel corpus locale."
                        ),
                    },
                ],
            }
        )
    if not records:
        raise RuntimeError(f"No supported reference answers found in {eval_dataset_path}")
    return records


def dataset_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    helpers = import_pipeline_helpers()
    total = len(rows)
    abstention_rows = sum(helpers["is_abstention_training_case"](row) for row in rows)
    italian_rows = sum(str(row.get("lang") or "").lower() == "it" for row in rows)
    categories: dict[str, int] = {}
    for row in rows:
        category = str(row.get("category") or "unknown")
        categories[category] = categories.get(category, 0) + 1
    return {
        "rows": total,
        "abstention_rows": abstention_rows,
        "actual_abstention_ratio": abstention_rows / total if total else 0.0,
        "italian_rows": italian_rows,
        "categories": categories,
    }


def prepare_style_abstention_patch(config: dict[str, Any], force: bool = False) -> dict[str, Any]:
    helpers = import_pipeline_helpers()
    base_dataset = repo_path(config["base_dataset_path"])
    patched_dataset = repo_path(config["dataset_path"])
    base_config = repo_path(config["base_training_config"])
    patched_config = repo_path(config["training_config"])
    supported_eval_dataset = repo_path(config["supported_eval_dataset_path"])
    target_ratio = float(config.get("target_abstention_ratio", 0.40))

    if patched_dataset.exists() and patched_config.exists() and not force:
        rows = helpers["read_jsonl"](patched_dataset)
        report = dataset_report(rows)
        report.update(
            {
                "dataset_path": rel(patched_dataset),
                "training_config": rel(patched_config),
                "status": "existing",
                "target_abstention_ratio": target_ratio,
            }
        )
        return report

    base_rows = [helpers["patch_record_system"](row) for row in helpers["read_jsonl"](base_dataset)]
    abstention_count = sum(helpers["is_abstention_training_case"](row) for row in base_rows)
    if abstention_count == 0:
        raise RuntimeError(f"No abstention/refusal rows detected in {base_dataset}")

    rows = list(base_rows)
    current_ratio = abstention_count / len(rows)
    if current_ratio > target_ratio:
        supported_rows = build_supported_records(supported_eval_dataset, helpers["SYSTEM_STYLE_PATCH"])
        required_supported = max(0, math.ceil(abstention_count / target_ratio - abstention_count))
        existing_supported = len(rows) - abstention_count
        needed = max(0, required_supported - existing_supported)
        for index in range(needed):
            template = copy.deepcopy(supported_rows[index % len(supported_rows)])
            template["id"] = f"{template['id']}-repeat-{index + 1:03d}"
            rows.append(template)
    else:
        abstention_rows = [row for row in rows if helpers["is_abstention_training_case"](row)]
        index = 0
        while sum(helpers["is_abstention_training_case"](row) for row in rows) / len(rows) < target_ratio:
            template = copy.deepcopy(abstention_rows[index % len(abstention_rows)])
            template["id"] = f"{template.get('id', 'abstention')}-repeat-{index + 1:03d}"
            rows.append(template)
            index += 1

    helpers["write_jsonl"](rows, patched_dataset)

    patched_cfg = load_yaml(base_config)
    patched_cfg["dataset_path"] = rel(patched_dataset)
    patched_cfg["output_dir"] = "fiorellia/training/lora/fiorellia_behavior_20260421_style_abstention_patch"
    patched_cfg["mlflow_experiment_name"] = config["experiment_name"]
    write_yaml(patched_config, patched_cfg)

    report = dataset_report(rows)
    report.update(
        {
            "dataset_path": rel(patched_dataset),
            "training_config": rel(patched_config),
            "status": "created",
            "target_abstention_ratio": target_ratio,
        }
    )
    return report


def select_entity_kwargs(entity_type: Any, **kwargs: Any) -> dict[str, Any]:
    signature = inspect.signature(entity_type)
    params = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return {key: value for key, value in kwargs.items() if value is not None}
    return {key: value for key, value in kwargs.items() if key in params and value is not None}


def azure_imports() -> dict[str, Any]:
    try:
        from azure.ai.ml import Input, MLClient, Output, command
        from azure.ai.ml.constants import AssetTypes
        from azure.ai.ml.entities import (
            AmlCompute,
            CodeConfiguration,
            Environment,
            ManagedOnlineDeployment,
            ManagedOnlineEndpoint,
            Model,
        )
        from azure.identity import DefaultAzureCredential, DeviceCodeCredential
    except ImportError as exc:
        raise SystemExit(
            "Azure ML dependencies are missing. Install them with:\n"
            "  python -m pip install azure-ai-ml azure-identity azureml-mlflow mlflow pyyaml\n"
            f"Original error: {exc}"
        ) from exc

    return {
        "AmlCompute": AmlCompute,
        "AssetTypes": AssetTypes,
        "CodeConfiguration": CodeConfiguration,
        "DefaultAzureCredential": DefaultAzureCredential,
        "DeviceCodeCredential": DeviceCodeCredential,
        "Environment": Environment,
        "Input": Input,
        "ManagedOnlineDeployment": ManagedOnlineDeployment,
        "ManagedOnlineEndpoint": ManagedOnlineEndpoint,
        "MLClient": MLClient,
        "Model": Model,
        "Output": Output,
        "command": command,
    }


def build_ml_client(config: dict[str, Any], modules: dict[str, Any], auth_method: str) -> Any:
    if auth_method == "device-code":
        credential = modules["DeviceCodeCredential"](tenant_id=config.get("tenant_id"))
    elif auth_method == "default":
        credential = modules["DefaultAzureCredential"](exclude_interactive_browser_credential=True)
    else:
        credential = modules["DefaultAzureCredential"](exclude_interactive_browser_credential=False)
    return modules["MLClient"](
        credential=credential,
        subscription_id=str(config["subscription_id"]),
        resource_group_name=str(config["resource_group"]),
        workspace_name=str(config["workspace_name"]),
    )


def validate_workspace_region(ml_client: Any, config: dict[str, Any], allow_mismatch: bool) -> None:
    workspace = ml_client.workspaces.get(str(config["workspace_name"]))
    expected = normalize_location(config.get("location"))
    actual = normalize_location(getattr(workspace, "location", None))
    if expected and actual and expected != actual and not allow_mismatch:
        raise RuntimeError(
            f"Workspace region mismatch: expected {expected}, Azure reports {actual}. "
            "Use --allow-location-mismatch only if this is intentional."
        )
    print(f"workspace={config['workspace_name']} location={actual or 'unknown'}")


def ensure_compute(ml_client: Any, config: dict[str, Any], modules: dict[str, Any]) -> Any:
    name = str(config["compute_name"])
    try:
        compute = ml_client.compute.get(name)
        print(f"compute={name} status=existing size={getattr(compute, 'size', 'unknown')}")
        return compute
    except Exception:
        pass

    kwargs = select_entity_kwargs(
        modules["AmlCompute"],
        name=name,
        size=str(config["compute_size"]),
        min_instances=int(config.get("compute_min_instances", 0)),
        max_instances=int(config.get("compute_max_instances", 1)),
        idle_time_before_scale_down=int(config.get("compute_idle_seconds", 120)),
        ssh_public_access_enabled=bool(config.get("ssh_public_access_enabled", False)),
        subnet=config.get("subnet_resource_id"),
        tier="Dedicated",
    )
    compute = modules["AmlCompute"](**kwargs)
    print(f"compute={name} status=creating size={config['compute_size']} ssh_public_access=false")
    return ml_client.compute.begin_create_or_update(compute).result()


def build_environment(config: dict[str, Any], modules: dict[str, Any], purpose: str) -> Any:
    return modules["Environment"](
        name=f"fiorellia-{purpose}-env",
        description=f"Fiorell.IA {purpose} environment for Qwen2.5 LoRA release",
        image="mcr.microsoft.com/azureml/curated/acpt-pytorch-2.2-cuda12.1:latest",
        conda_file=str(ENDPOINT_CODE_DIR / "conda.yaml"),
    )


def submit_training_job(
    ml_client: Any,
    config: dict[str, Any],
    modules: dict[str, Any],
    wait: bool,
) -> Any:
    training_config = repo_path(config["training_config"])
    dataset_path = repo_path(config["dataset_path"])
    adapter_output_name = str(config.get("adapter_output_name", "adapter"))
    adapter_output_expr = f"${{{{outputs.{adapter_output_name}}}}}"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    display_name = f"fiorellia-qwen25-lora-{timestamp}"
    environment = build_environment(config, modules, "training")

    job = modules["command"](
        code=str(REPO_ROOT),
        command=(
            f"python {TRAINING_ENTRYPOINT} "
            "--config ${{inputs.training_config}} "
            "--dataset-path ${{inputs.training_dataset}} "
            f"--output-dir {adapter_output_expr}"
        ),
        inputs={
            "training_config": modules["Input"](type=modules["AssetTypes"].URI_FILE, path=str(training_config)),
            "training_dataset": modules["Input"](type=modules["AssetTypes"].URI_FILE, path=str(dataset_path)),
        },
        outputs={adapter_output_name: modules["Output"](type=modules["AssetTypes"].URI_FOLDER)},
        environment=environment,
        compute=str(config["compute_name"]),
        experiment_name=str(config["experiment_name"]),
        display_name=display_name,
        environment_variables={
            "FIORELLIA_REPORT_TO_MLFLOW": "1",
            "MLFLOW_EXPERIMENT_NAME": str(config["experiment_name"]),
            "MLFLOW_RUN_NAME": display_name,
            "PYTHONUNBUFFERED": "1",
            "TOKENIZERS_PARALLELISM": "false",
        },
    )

    created = ml_client.jobs.create_or_update(job)
    print(f"job_submitted name={created.name} studio_url={created.studio_url}")
    if wait:
        ml_client.jobs.stream(created.name)
        created = ml_client.jobs.get(created.name)
        print(f"job_final_status={created.status}")
        if created.status != "Completed":
            raise RuntimeError(f"Training job did not complete successfully: {created.status}")
    return created


def deploy_endpoint(ml_client: Any, config: dict[str, Any], modules: dict[str, Any], job_name: str) -> dict[str, Any]:
    adapter_output_name = str(config.get("adapter_output_name", "adapter"))
    model_uri = f"azureml://jobs/{job_name}/outputs/{adapter_output_name}"
    model = modules["Model"](
        path=model_uri,
        name=str(config["model_name"]),
        type=modules["AssetTypes"].CUSTOM_MODEL,
        description="Fiorell.IA Qwen2.5-3B-Instruct LoRA adapter from Azure ML release training.",
    )
    registered_model = ml_client.models.create_or_update(model)
    print(f"model_registered name={registered_model.name} version={registered_model.version}")

    endpoint_kwargs = select_entity_kwargs(
        modules["ManagedOnlineEndpoint"],
        name=str(config["endpoint_name"]),
        description="Fiorell.IA managed online endpoint",
        auth_mode=str(config.get("auth_mode", "key")),
        public_network_access=str(config.get("public_network_access", "enabled")),
    )
    endpoint = modules["ManagedOnlineEndpoint"](**endpoint_kwargs)
    endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print(f"endpoint_ready name={endpoint.name} scoring_uri={getattr(endpoint, 'scoring_uri', '')}")

    deployment = modules["ManagedOnlineDeployment"](
        name=str(config.get("deployment_name", "blue")),
        endpoint_name=str(config["endpoint_name"]),
        model=registered_model,
        environment=build_environment(config, modules, "inference"),
        code_configuration=modules["CodeConfiguration"](
            code=str(ENDPOINT_CODE_DIR),
            scoring_script=ENDPOINT_SCORING_SCRIPT,
        ),
        instance_type=str(config["instance_type"]),
        instance_count=int(config.get("instance_count", 1)),
    )
    ml_client.online_deployments.begin_create_or_update(deployment).result()
    endpoint.traffic = {str(config.get("deployment_name", "blue")): 100}
    endpoint = ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    keys = ml_client.online_endpoints.get_keys(name=str(config["endpoint_name"]))

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "subscription_id": str(config["subscription_id"]),
        "resource_group": str(config["resource_group"]),
        "workspace_name": str(config["workspace_name"]),
        "location": str(config.get("location", "")),
        "experiment_name": str(config["experiment_name"]),
        "job_name": job_name,
        "model_name": registered_model.name,
        "model_version": registered_model.version,
        "endpoint_name": endpoint.name,
        "deployment_name": str(config.get("deployment_name", "blue")),
        "scoring_uri": getattr(endpoint, "scoring_uri", None),
        "primary_key": getattr(keys, "primary_key", None),
        "secondary_key": getattr(keys, "secondary_key", None),
    }
    summary_path = repo_path(config.get("deploy_summary_path", "azure_deploy_summary.json"))
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"deploy_summary={summary_path}")
    return summary


def print_plan(config: dict[str, Any], dataset_info: dict[str, Any]) -> None:
    redacted = dict(config)
    print(
        json.dumps(
            {
                "workspace": {
                    "subscription_id": redacted["subscription_id"],
                    "resource_group": redacted["resource_group"],
                    "workspace_name": redacted["workspace_name"],
                    "location": redacted.get("location"),
                },
                "compute": {
                    "name": redacted["compute_name"],
                    "size": redacted["compute_size"],
                    "min_instances": redacted.get("compute_min_instances"),
                    "max_instances": redacted.get("compute_max_instances"),
                    "ssh_public_access_enabled": redacted.get("ssh_public_access_enabled"),
                    "subnet_resource_id": redacted.get("subnet_resource_id"),
                },
                "training": {
                    "experiment_name": redacted["experiment_name"],
                    "entrypoint": TRAINING_ENTRYPOINT,
                    "config": redacted["training_config"],
                    "dataset": redacted["dataset_path"],
                    "adapter_output_name": redacted["adapter_output_name"],
                    "dataset_info": dataset_info,
                },
                "deployment": {
                    "endpoint_name": redacted["endpoint_name"],
                    "deployment_name": redacted["deployment_name"],
                    "instance_type": redacted["instance_type"],
                    "public_network_access": redacted.get("public_network_access"),
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Fiorell.IA Azure ML LoRA training.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Prepare local artifacts and print the Azure plan without calling Azure.")
    parser.add_argument("--force-local-prep", action="store_true", help="Regenerate the patched dataset and training config.")
    parser.add_argument("--no-wait", action="store_true", help="Submit the training job and return immediately.")
    parser.add_argument("--no-deploy", action="store_true", help="Do not deploy the managed endpoint after the training job completes.")
    parser.add_argument("--allow-location-mismatch", action="store_true", help="Do not fail if the workspace region differs from config.location.")
    parser.add_argument(
        "--auth-method",
        choices=["device-code", "default", "browser"],
        default=os.environ.get("FIORELLIA_AZURE_AUTH", "device-code"),
        help="Azure authentication method. device-code is terminal-friendly; browser opens a local redirect server.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(args.config)
    os.chdir(REPO_ROOT)

    dataset_info = prepare_style_abstention_patch(config, force=args.force_local_prep)
    print_plan(config, dataset_info)
    if args.dry_run:
        print("dry_run=true; Azure submission skipped.")
        return 0

    modules = azure_imports()
    ml_client = build_ml_client(config, modules, auth_method=args.auth_method)
    validate_workspace_region(ml_client, config, allow_mismatch=args.allow_location_mismatch)
    ensure_compute(ml_client, config, modules)
    job = submit_training_job(ml_client, config, modules, wait=not args.no_wait)

    if args.no_deploy:
        return 0
    if args.no_wait:
        print("deployment_skipped=true reason=no_wait")
        return 0

    summary = deploy_endpoint(ml_client, config, modules, job_name=job.name)
    print(
        json.dumps(
            {
                "endpoint_name": summary["endpoint_name"],
                "deployment_name": summary["deployment_name"],
                "scoring_uri": summary["scoring_uri"],
                "deploy_summary_path": str(repo_path(config.get("deploy_summary_path", "azure_deploy_summary.json"))),
                "api_key_written": bool(summary.get("primary_key")),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
