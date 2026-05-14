"""Fiorell.IA NO-GO recovery runbook.

Run from Colab after cloning the repository. The script performs the safe phases
needed after a NO-GO evaluation:

1. preflight config/dataset/GPU;
2. optional eval metric debugging if eval output exists;
3. creation of a patched SFT dataset with stricter Italian style instructions;
4. creation of a patched config pointing to the new dataset;
5. creation of leave-one-category-out ablation datasets/configs;
6. final artifact report.

It does not launch long training/eval automatically. Training remains delegated
to the existing train_lora_behavior_v1.py script and eval remains delegated to
the existing eval harness/notebook.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fiorellia.training.fiorellia_colab_pipeline import (
    build_style_abstention_dataset,
    check_cuda,
    load_config,
    read_jsonl,
    require_file,
    save_config,
    score_eval_rows,
    validate_config,
    write_ablation_datasets,
    write_csv,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fiorell.IA NO-GO recovery runbook")
    parser.add_argument("--repo-root", default="/content/regulatory-insight-engine")
    parser.add_argument(
        "--config",
        default="fiorellia/training/configs/config_lora_behavior_20260421.yaml",
    )
    parser.add_argument("--artifact-root", default="/content/drive/MyDrive/fiorellia/artifacts")
    parser.add_argument("--eval-jsonl", default="/content/drive/MyDrive/fiorellia/artifacts/eval_adapter.jsonl")
    parser.add_argument("--target-abstention-ratio", type=float, default=0.40)
    parser.add_argument("--skip-gpu-check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    config_path = (repo_root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config).resolve()
    artifact_root = Path(args.artifact_root).expanduser().resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)

    print("=== Fiorell.IA NO-GO recovery runbook ===")
    print("repo_root:", repo_root)
    print("config_path:", config_path)
    print("artifact_root:", artifact_root)

    if not args.skip_gpu_check:
        print("\n[1] GPU preflight")
        print(json.dumps(check_cuda(require_gpu=True), indent=2, ensure_ascii=False))

    print("\n[2] Config/dataset preflight")
    config = load_config(config_path)
    resolved = validate_config(config, repo_root)
    print("dataset:", resolved["dataset_path"])
    print("output_dir:", resolved["output_dir"])

    print("\n[3] Eval metric debug")
    eval_jsonl = Path(args.eval_jsonl).expanduser().resolve()
    if eval_jsonl.exists():
        rows = read_jsonl(eval_jsonl)
        scored_rows, debug_metrics = score_eval_rows(rows)
        debug_metrics_path = artifact_root / "debug_metrics.json"
        scored_eval_path = artifact_root / "eval_adapter_scored.jsonl"
        write_json(debug_metrics, debug_metrics_path)
        from fiorellia.training.fiorellia_colab_pipeline import write_jsonl

        write_jsonl(scored_rows, scored_eval_path)
        print(json.dumps(debug_metrics, indent=2, ensure_ascii=False))
        print("debug_metrics:", debug_metrics_path)
        print("scored_eval:", scored_eval_path)
        counts = debug_metrics.get("subset_counts", {})
        if any(counts.get(k, 0) == 0 for k in ["in_scope", "unsupported", "out_of_scope"]):
            print("WARNING: one or more benchmark subsets are empty. NaN is likely caused by label/category mapping.")
    else:
        print("Eval JSONL not found; skipping metric debug:", eval_jsonl)

    print("\n[4] Create style + abstention patched SFT dataset")
    patched_dataset = repo_root / "fiorellia/training/supervised_v1_curated_20260421_style_abstention_patch.jsonl"
    dataset_report = build_style_abstention_dataset(
        resolved["dataset_path"],
        patched_dataset,
        target_abstention_ratio=args.target_abstention_ratio,
    )
    print(json.dumps(dataset_report, indent=2, ensure_ascii=False))

    print("\n[5] Create patched config")
    patched_config = repo_root / "fiorellia/training/configs/config_lora_behavior_20260421_style_abstention_patch.yaml"
    patched_cfg = dict(config)
    patched_cfg["dataset_path"] = str(patched_dataset.relative_to(repo_root))
    patched_cfg["output_dir"] = "fiorellia/training/lora/fiorellia_behavior_20260421_style_abstention_patch"
    save_config(patched_cfg, patched_config)
    print("patched_config:", patched_config)

    print("\n[6] Create ablation datasets")
    ablation_root = artifact_root / "ablation"
    ablation_datasets = write_ablation_datasets(patched_dataset, ablation_root / "datasets")
    ablation_dataset_report = ablation_root / "ablation_dataset_report.csv"
    write_csv(ablation_datasets, ablation_dataset_report)
    print("ablation_dataset_report:", ablation_dataset_report)

    print("\n[7] Create ablation configs")
    config_rows = []
    config_dir = ablation_root / "configs"
    adapter_dir = ablation_root / "adapters"
    config_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir.mkdir(parents=True, exist_ok=True)

    for row in ablation_datasets:
        removed = row["removed_category"]
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in removed)
        cfg = dict(patched_cfg)
        ds_path = Path(row["dataset_path"])
        cfg["dataset_path"] = str(ds_path.relative_to(repo_root)) if str(ds_path).startswith(str(repo_root)) else str(ds_path)
        cfg["output_dir"] = str(adapter_dir / f"without__{safe}")
        cfg["num_train_epochs"] = 1
        cfg["save_strategy"] = "no"
        cfg["logging_steps"] = 10
        out_cfg = config_dir / f"without__{safe}.yaml"
        save_config(cfg, out_cfg)
        config_rows.append({"removed_category": removed, "config_path": str(out_cfg), "output_dir": cfg["output_dir"]})

    ablation_config_report = ablation_root / "ablation_config_report.csv"
    write_csv(config_rows, ablation_config_report)
    print("ablation_config_report:", ablation_config_report)

    final_report = {
        "patched_dataset": str(patched_dataset),
        "patched_config": str(patched_config),
        "dataset_report": dataset_report,
        "ablation_dataset_report": str(ablation_dataset_report),
        "ablation_config_report": str(ablation_config_report),
        "next_training_command": f"python fiorellia/training/train_lora_behavior_v1.py --config {patched_config}",
    }
    final_report_path = artifact_root / "no_go_recovery_report.json"
    write_json(final_report, final_report_path)

    print("\n=== DONE ===")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    print("final_report:", final_report_path)


if __name__ == "__main__":
    main()
