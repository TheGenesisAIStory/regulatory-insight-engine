# Training preparation (optional, offline)

Questa cartella contiene strumenti leggeri per preparare dati e artefatti in vista di una domain adaptation locale (LoRA / instruction tuning / lightweight tuning). Tutto è pensato per essere opzionale e separato dal runtime RAG di produzione.

Struttura:

- `training/config/` — configurazioni (JSON)
- `training/data/` — dati di lavoro, output e artefatti
- `training/scripts/` — script per validazione, split, esportazione e salvataggio artefatti

Principi:
- Offline-first: nessuna dipendenza cloud obbligatoria.
- Disaccoppiato dal runtime RAG: nessuno script modifica il codice di `backend/` o il comportamento dell'API.
- Piccoli e modulari: gli script sono wrappers che usano il dataset supervisionato esistente (`backend/eval/`).

Uso rapido (da root del repo):

1. Controlla/aggiorna la configurazione in `training/config/config.json`.
2. Validare il dataset (usa il validator canonico):

```bash
python backend/eval/validate_supervised_dataset.py --input backend/eval/supervised_seed.jsonl --output backend/eval/supervised_seed.cleaned.jsonl
```

3. Creare split train/validation:

```bash
python training/scripts/split_dataset.py --config training/config/config.json
```

4. Esportare in formato instruction-tuning (Alpaca-style):

```bash
python training/scripts/export_instruction_tuning.py --input training/data/train.jsonl --output training/data/output/instruction_train.jsonl
```

5. Salvare artefatti e metriche:

```bash
python training/scripts/save_artifacts.py --input training/data --output training/data/output
```

Vedi i singoli script in `training/scripts/` per opzioni avanzate.
