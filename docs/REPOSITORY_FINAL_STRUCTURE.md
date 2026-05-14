# Struttura finale del repository

Questa pagina definisce la struttura finale consigliata per `regulatory-insight-engine`.

Root locale ufficiale:

```text
/Users/itsgennymac/Documents/GitHub/regulatory-insight-engine
```

## Obiettivo della struttura

Il repository deve essere chiaro per tre tipi di utenti:

1. chi usa Colab e vuole solo addestrare/valutare Fiorell.IA;
2. chi lavora sul motore RAG locale;
3. chi deve revisionare audit, output e decisioni GO/NO-GO.

## Struttura finale consigliata

```text
regulatory-insight-engine/
├── README.md
├── AGENTS.md
├── backend/
│   ├── api.py
│   ├── genisia_rag_engine.py
│   ├── eval/
│   └── README.md
├── docs/
│   ├── REPOSITORY_FINAL_STRUCTURE.md
│   ├── FIORELLIA_TRAINING_GUIDE.md
│   ├── FIORELLIA_EVAL_GUIDE.md
│   ├── LOCAL_GITHUB_SYNC.md
│   ├── RELEASE_CHECKLIST.md
│   ├── RUNTIME_RAG.md
│   ├── EVALUATION.md
│   └── PRODUCTION_EXPERIMENTAL.md
├── fiorellia/
│   ├── README.md
│   ├── prompts/
│   ├── training/
│   │   ├── 01_start_here_training_export.ipynb
│   │   ├── fiorellia_colab_pipeline.py
│   │   ├── fiorellia_nogo_recovery_runbook.ipynb
│   │   ├── configs/
│   │   └── supervised_v1_curated_20260421.jsonl
│   └── eval/
│       ├── 02_start_here_eval_decision.ipynb
│       └── eval set / baseline versionabili
├── src/
├── package.json
└── LICENSE
```

## File da tenere

Tenere sempre:

- `README.md` root;
- `fiorellia/README.md`;
- `fiorellia/training/01_start_here_training_export.ipynb`;
- `fiorellia/eval/02_start_here_eval_decision.ipynb`;
- `fiorellia/training/fiorellia_colab_pipeline.py`;
- `fiorellia/training/configs/config_lora_behavior_20260421.yaml`;
- guide in `docs/`;
- backend RAG e benchmark in `backend/`.

## File da archiviare

Archiviare, ma non cancellare subito, notebook precedenti o sperimentali come:

```text
fiorellia_lora_colab_ok*.ipynb
fiorellia_eval_adapter*.ipynb
*_draft.ipynb
*_old.ipynb
*_backup.ipynb
```

Posizione consigliata:

```text
fiorellia/archive/
```

Motivo: possono contenere storia utile, ma non devono essere il punto di ingresso per utenti finali.

## File da non committare normalmente

Non committare:

```text
artifacts/
outputs/
*.zip
*.safetensors
adapter_model.bin
adapter_model.safetensors
metrics_summary.json generati da run locali
final_verdict.md generati da run locali
*_scored_eval_rows.jsonl
```

Questi file sono output di esecuzione e possono essere pesanti o variabili.

## Convenzione artifact

In Colab usare:

```text
/content/drive/MyDrive/fiorellia/training_final/
/content/drive/MyDrive/fiorellia/eval_final/
/content/drive/MyDrive/fiorellia/nogo_recovery/
```

In locale usare:

```text
/Users/itsgennymac/Documents/GitHub/regulatory-insight-engine/artifacts/fiorellia/
```

## Regola finale

Un utente nuovo deve aprire solo due notebook:

```text
fiorellia/training/01_start_here_training_export.ipynb
fiorellia/eval/02_start_here_eval_decision.ipynb
```

Ogni altro notebook è di supporto, storico o recovery.
