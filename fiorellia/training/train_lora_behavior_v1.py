#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
import random
from pathlib import Path
from typing import Any

import torch
import yaml
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_v1.yaml"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if "messages" not in record:
                raise ValueError(f"Missing messages at {path}:{line_no}")
            records.append(record)
    return records


def render_chat(tokenizer: AutoTokenizer, messages: list[dict[str, str]]) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
    rendered = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        rendered.append(f"<|{role}|>\n{content}")
    return "\n".join(rendered) + "\n<|end|>"


def build_dataset(records: list[dict[str, Any]], tokenizer: AutoTokenizer, max_seq_length: int) -> Dataset:
    texts = [{"text": render_chat(tokenizer, record["messages"])} for record in records]
    dataset = Dataset.from_list(texts)

    def tokenize(batch: dict[str, list[str]]) -> dict[str, Any]:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_seq_length,
            padding=False,
        )

    return dataset.map(tokenize, batched=True, remove_columns=["text"])


def save_cpu_checkpoint(model: torch.nn.Module, tokenizer: AutoTokenizer, output_dir: Path, name: str) -> None:
    checkpoint_dir = output_dir / name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(checkpoint_dir))
    tokenizer.save_pretrained(str(checkpoint_dir))
    print(f"saved_checkpoint={checkpoint_dir}")


def train_cpu_loop(
    model: torch.nn.Module,
    tokenizer: AutoTokenizer,
    train_dataset: Dataset,
    eval_dataset: Dataset | None,
    config: dict[str, Any],
    output_dir: Path,
) -> None:
    print("CPU loop enabled: bypassing Trainer/Accelerate device wrapping.")
    model = model.to("cpu")
    model.train()

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    train_loader = DataLoader(
        train_dataset,
        batch_size=int(config["per_device_train_batch_size"]),
        shuffle=True,
        collate_fn=collator,
        pin_memory=False,
    )
    eval_loader = (
        DataLoader(
            eval_dataset,
            batch_size=1,
            shuffle=False,
            collate_fn=collator,
            pin_memory=False,
        )
        if eval_dataset is not None
        else None
    )

    optimizer = torch.optim.AdamW(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=float(config["learning_rate"]),
    )
    grad_acc = max(1, int(config["gradient_accumulation_steps"]))
    epochs = int(float(config["num_train_epochs"]))
    logging_steps = max(1, int(config["logging_steps"]))
    global_step = 0

    optimizer.zero_grad(set_to_none=True)
    for epoch in range(epochs):
        running_loss = 0.0
        for batch_index, batch in enumerate(train_loader, start=1):
            batch = {key: value.to("cpu") for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / grad_acc
            loss.backward()
            running_loss += float(loss.detach().cpu()) * grad_acc

            if batch_index % grad_acc == 0 or batch_index == len(train_loader):
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1
                if global_step % logging_steps == 0 or global_step == 1:
                    avg_loss = running_loss / batch_index
                    print(f"epoch={epoch + 1} step={global_step} train_loss={avg_loss:.6f}")

        if eval_loader is not None:
            model.eval()
            eval_loss = 0.0
            with torch.no_grad():
                for eval_batch in eval_loader:
                    eval_batch = {key: value.to("cpu") for key, value in eval_batch.items()}
                    eval_loss += float(model(**eval_batch).loss.detach().cpu())
            print(f"epoch={epoch + 1} eval_loss={eval_loss / max(1, len(eval_loader)):.6f}")
            model.train()

        save_cpu_checkpoint(model, tokenizer, output_dir, f"checkpoint-epoch-{epoch + 1}")

    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"saved_adapter={output_dir}")


def split_records(records: list[dict[str, Any]], seed: int, validation_split_ratio: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not records:
        raise ValueError("Training dataset is empty.")
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    if len(shuffled) < 5 or validation_split_ratio <= 0:
        return shuffled, []
    validation_size = max(1, int(round(len(shuffled) * validation_split_ratio)))
    validation_size = min(validation_size, len(shuffled) - 1)
    return shuffled[validation_size:], shuffled[:validation_size]


def load_model(config: dict[str, Any]) -> AutoModelForCausalLM:
    has_cuda = torch.cuda.is_available()
    has_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    allow_mps = bool(config.get("allow_mps", False))
    dtype = torch.bfloat16 if has_cuda else torch.float32
    model_kwargs: dict[str, Any] = {
        "torch_dtype": dtype,
        "low_cpu_mem_usage": True,
    }

    use_4bit = False
    if config.get("use_4bit", False) and has_cuda:
        try:
            from transformers import BitsAndBytesConfig
            import bitsandbytes  # noqa: F401

            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            model_kwargs["device_map"] = "auto"
            use_4bit = True
        except Exception as exc:
            print(f"4-bit loading unavailable, continuing without quantization: {exc}")
    elif config.get("use_4bit", False):
        print("4-bit loading skipped: CUDA is not available on this machine.")

    model = AutoModelForCausalLM.from_pretrained(config["base_model_name"], **model_kwargs)
    if has_mps and allow_mps and not use_4bit:
        try:
            model = model.to("mps")
            print("MPS enabled: model moved to mps.")
        except RuntimeError as exc:
            print(f"MPS move failed, falling back to CPU: {exc}")
            model = model.to("cpu")
    elif has_mps and not allow_mps:
        print("MPS available but disabled by config allow_mps=false; keeping model on CPU.")
    model.config.use_cache = False
    if use_4bit:
        model = prepare_model_for_kbit_training(model)
    return model


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Fiorell.IA behavior LoRA v1.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = load_config(args.config)
    dataset_path = ROOT / config["dataset_path"]
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"config={args.config}")
    print(f"dataset={dataset_path}")
    print(f"output_dir={output_dir}")
    print(f"base_model={config['base_model_name']}")

    tokenizer = AutoTokenizer.from_pretrained(config["base_model_name"], use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    records = load_jsonl(dataset_path)
    train_records, eval_records = split_records(
        records,
        seed=int(config.get("seed", 42)),
        validation_split_ratio=float(config.get("validation_split_ratio", 0.0)),
    )
    print(f"records_total={len(records)}")
    print(f"records_train={len(train_records)}")
    print(f"records_eval={len(eval_records)}")

    train_dataset = build_dataset(train_records, tokenizer, int(config["max_seq_length"]))
    eval_dataset = (
        build_dataset(eval_records, tokenizer, int(config["max_seq_length"]))
        if eval_records
        else None
    )
    model = load_model(config)

    lora_config = LoraConfig(
        r=int(config["lora_r"]),
        lora_alpha=int(config["lora_alpha"]),
        lora_dropout=float(config["lora_dropout"]),
        target_modules=config.get("target_modules"),
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    allow_mps = bool(config.get("allow_mps", False))
    if not allow_mps:
        model = model.to("cpu")
        print("CPU device guard: allow_mps=false, keeping PEFT model on CPU.")
    model.print_trainable_parameters()

    if not allow_mps and not torch.cuda.is_available():
        train_cpu_loop(model, tokenizer, train_dataset, eval_dataset, config, output_dir)
        return 0

    training_kwargs: dict[str, Any] = {
        "output_dir": str(output_dir),
        "num_train_epochs": float(config["num_train_epochs"]),
        "per_device_train_batch_size": int(config["per_device_train_batch_size"]),
        "gradient_accumulation_steps": int(config["gradient_accumulation_steps"]),
        "learning_rate": float(config["learning_rate"]),
        "warmup_ratio": float(config["warmup_ratio"]),
        "logging_steps": int(config["logging_steps"]),
        "save_steps": int(config["save_steps"]),
        "save_strategy": config.get("save_strategy", "steps"),
        "save_total_limit": int(config.get("save_total_limit", 2)),
        "bf16": torch.cuda.is_available(),
        "fp16": False,
        "dataloader_pin_memory": False,
        "report_to": [],
        "remove_unused_columns": False,
        "seed": int(config.get("seed", 42)),
    }
    eval_value = config.get("eval_strategy", "no") if eval_dataset is not None else "no"
    training_signature = inspect.signature(TrainingArguments)
    if not allow_mps:
        if "use_cpu" in training_signature.parameters:
            training_kwargs["use_cpu"] = True
        if "no_cuda" in training_signature.parameters:
            training_kwargs["no_cuda"] = True
        if "use_mps_device" in training_signature.parameters:
            training_kwargs["use_mps_device"] = False
    if "eval_strategy" in training_signature.parameters:
        training_kwargs["eval_strategy"] = eval_value
    else:
        training_kwargs["evaluation_strategy"] = eval_value
    training_args = TrainingArguments(**training_kwargs)
    if not allow_mps:
        try:
            training_args.device = torch.device("cpu")
        except Exception:
            pass
        print(f"Trainer device guard: allow_mps=false, Trainer device={training_args.device}.")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"saved_adapter={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
