# Training data

Questa cartella contiene i file temporanei e gli output prodotti durante la preparazione dei dati per il training.

- `training/data/train.jsonl` — split di training
- `training/data/val.jsonl` — split di validation
- `training/data/fiorellia_supervised_seed_v1.jsonl` — seed supervisionato Fiorell.IA in formato chat-style per LoRA/QLoRA leggero
- `training/data/output/` — artefatti esportati (instruction jsonl, metriche, copie dei dataset)

Non check-inare file binari pesanti; mantieni qui solo artefatti locali e versionabili leggeri.

Per misurare le categorie del seed con il benchmark locale, genera la vista compatibile con `backend/eval/run_benchmark.py`:

```bash
python3 backend/eval/build_fiorellia_seed_eval.py
```

Il file derivato viene scritto in:

```text
backend/eval/fiorellia_supervised_seed_eval.jsonl
```
