# Fiorell.IA — Training ed Eval LoRA user-friendly

Fiorell.IA è la traccia sperimentale del repository dedicata all’allineamento LoRA di un modello Qwen per rispondere su normativa bancaria italiana in modo prudente, tracciabile e conservativo.

## Obiettivo

Il modello deve:

- rispondere in italiano;
- usare tono formale, tecnico e conciso;
- rispondere solo quando le fonti locali recuperate supportano la risposta;
- astenersi quando la domanda è fuori ambito o le fonti non sono sufficienti;
- non inventare riferimenti normativi, citazioni o pagine.

## Per utenti non tecnici

Usa solo questi due notebook:

```text
fiorellia/training/01_start_here_training_export.ipynb
fiorellia/eval/02_start_here_eval_decision.ipynb
```

Esegui le celle dall’alto verso il basso. Non serve modificare script Python.

## Training

Guida completa:

```text
docs/FIORELLIA_TRAINING_GUIDE.md
```

Output atteso:

```text
fiorellia_lora_adapter.zip
training_summary.json
training_final_summary.md
```

## Eval

Guida completa:

```text
docs/FIORELLIA_EVAL_GUIDE.md
```

Script finale Colab/Drive:

```text
fiorellia/eval/colab_drive_final_eval.py
```

Output atteso:

```text
eval_adapter_scored.jsonl
comparison.csv
metrics_summary.json
final_verdict.md
```

## Decisione finale

Il run è **GO** solo se:

- adapter ZIP valido;
- eval completata;
- priority cases preservati;
- soglie metriche rispettate;
- nessun artifact critico mancante.

In ogni altro caso il risultato è **NO-GO**.

## File principali

```text
fiorellia/training/fiorellia_colab_pipeline.py
```

Contiene funzioni comuni per:

- preflight;
- validazione config;
- validazione adapter;
- debug metriche;
- patch dataset stile italiano/abstention;
- ablation datasets;
- scrittura summary finali.

```text
fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

Config principale validata.

```text
fiorellia/training/fiorellia_nogo_recovery_runbook.ipynb
```

Da usare solo se l’eval produce NO-GO, metriche NaN, italian_style basso o unsupported_abstention insufficiente.

## Boundary

Fiorell.IA non sostituisce il RAG runtime condiviso in `backend/`. Il training LoRA resta una traccia sperimentale e separata dal serving locale.

## Regola operativa

Non modificare il comportamento del modello direttamente nei notebook. Se serve una modifica, falla in modo controllato tramite config o helper versionati.

## Disclaimer

Fiorell.IA non fornisce consulenza legale, contabile, regolamentare o di vigilanza. Ogni risposta deve essere verificata sulle fonti ufficiali.
