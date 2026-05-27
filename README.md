# Regulatory Insight Engine — Gen.Is.IA / Fiorell.IA

Assistente AI offline-first per interrogare normativa bancaria e finanziaria con approccio RAG, tracciabilità delle fonti e comportamento conservativo di astensione quando le fonti non sono sufficienti.

Il repository contiene due livelli complementari:

1. **Regulatory Insight Engine / Gen.Is.IA**  
   Motore RAG locale con backend FastAPI, UI React, corpus normativo, benchmark e controlli di readiness.

2. **Fiorell.IA**  
   Specializzazione sperimentale per training/eval LoRA su normativa bancaria italiana, con workflow Colab guidato, export adapter e decisione GO/NO-GO.

---

## Stato finale del repository

Il progetto è organizzato per essere usato in modo progressivo:

- utente non tecnico: usa i notebook Colab guidati;
- utente tecnico: usa script, backend, benchmark e runbook;
- reviewer/auditor: legge output, metriche, summary markdown e checklist.

La policy funzionale resta conservativa:

- rispondere solo se il contenuto è supportato da fonti locali recuperate;
- citare fonti e riferimenti quando disponibili;
- astenersi in modo esplicito se il supporto documentale non è sufficiente;
- non inventare contenuti normativi, citazioni o riferimenti.

Runbook attivo Fiorell.IA Colab A100:

```text
docs/FIORELLIA_COLAB_A100_RUNBOOK.md
```

Root operativa Drive per lavoro locale e Colab:

```text
/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine
/content/drive/MyDrive/regulatory-insight-engine
```

Notebook operativo per VS Code collegato a Colab A100:

```text
fiorellia_final_colab_a100_release.ipynb
```

Notebook Gold Release zero-touch:

```text
fiorellia_final_gold_release.ipynb
```

Il notebook Gold monta Drive, armonizza `/content/drive/MyDrive/regulatory-insight-engine`, archivia i verdict obsoleti, verifica CUDA/A100, bilancia il dataset Gold dopo la triplicazione delle astensioni, addestra con `num_train_epochs=10`, `learning_rate=3e-5`, `gradient_accumulation_steps=4`, salva lo ZIP in `releases/gold_release_latest/` e apre la demo Gradio solo dopo `GO DEFINITIVO` reale.

Per rivalutare una run Gold gia completata senza rifare training:

```bash
python fiorellia_gold_rescore_existing.py --copy-verdict-to-repo
```

Tutti i notebook Fiorell.IA attivi contengono una cella iniziale `00 - Fiorell.IA Drive-first bootstrap`, che forza il lavoro sulla root Drive e aggiorna automaticamente gli script critici se la copia Drive risulta mancante o stale.

Il flusso operativo Fiorell.IA attivo è solo Colab/Drive-first. Eventuali file storici di deployment cloud restano fuori dal percorso di training, eval e rilascio finale.

Il notebook finale salva sempre gli esiti reali su Drive. Se Colab non può autenticarsi su GitHub, scrive `github_publish_status.json` e lascia la pubblicazione al checkout locale autenticato. Se il verdict non è `GO DEFINITIVO`, scrive `app_launch_status.json` e non apre la UI pubblica Gradio.

Recovery behavior-hardening attivo dopo il `NO-GO` reale:

```text
fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl
fiorellia/training/configs/config_lora_behavior_20260526_behavior_hardening.yaml
fiorellia/prompts/system_prompt_strict.md
fiorellia/eval/eval_set_behavior_hardening_v1.jsonl
```

Recovery finale per analisi fallimenti, pulizia dataset, 20 esempi di astensione estrema,
grounded-recovery examples nel formato del prompt harness e retraining conservativo:

```text
final_perfection_run.py
fiorellia/training/supervised_v3_final_perfection_20260527.jsonl
fiorellia/training/configs/config_lora_behavior_20260527_final_perfection.yaml
```

Il prossimo run Colab produce un adapter versionato `fiorellia_behavior_FINAL_PERFECTION_20260527` senza sovrascrivere gli artefatti precedenti.

---

## Percorso consigliato per utenti non tecnici

Apri i notebook in Google Colab ed esegui le celle dall’alto verso il basso.

### 1. Training Fiorell.IA

Notebook principale:

```text
fiorellia/training/01_start_here_training_export.ipynb
```

Cosa fa:

- prepara l’ambiente Colab;
- controlla GPU, dataset e config;
- esegue training LoRA;
- esporta l’adapter in ZIP;
- salva un summary finale.

Guida:

```text
docs/FIORELLIA_TRAINING_GUIDE.md
```

### 2. Valutazione Fiorell.IA

Notebook principale:

```text
fiorellia/eval/02_start_here_eval_decision.ipynb
```

Cosa fa:

- controlla adapter ZIP, eval set, baseline e prompt;
- esegue o raccoglie output di valutazione;
- calcola metriche aggregate;
- controlla priority cases;
- produce decisione finale GO / NO-GO.

Guida:

```text
docs/FIORELLIA_EVAL_GUIDE.md
```

---

## Percorso per usare il RAG locale

Per backend/UI e benchmark RAG locale vedi:

```text
docs/RUNTIME_RAG.md
docs/EVALUATION.md
docs/CORPUS_LIFECYCLE.md
backend/README.md
```

Avvio rapido tecnico:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
npm install
npm run dev
```

---

## Struttura finale consigliata

```text
regulatory-insight-engine/
├── README.md
├── AGENTS.md
├── backend/                         # API, RAG engine, benchmark backend
├── docs/                            # guide operative e governance
├── fiorellia/
│   ├── README.md                    # guida specifica Fiorell.IA
│   ├── training/
│   │   ├── 01_start_here_training_export.ipynb
│   │   ├── fiorellia_colab_pipeline.py
│   │   ├── configs/
│   │   └── *.jsonl                  # dataset SFT versionati se non sensibili
│   └── eval/
│       ├── 02_start_here_eval_decision.ipynb
│       └── *.jsonl                  # eval set/baseline se versionabili
├── src/                             # UI React
├── package.json
└── pyproject / requirements ove presenti
```

Output e artifact generati non vanno normalmente committati:

```text
artifacts/
outputs/
*.zip adapter
*.safetensors
*_scored_eval_rows.jsonl
metrics_summary.json
final_verdict.md
```

---

## Documentazione principale

- `docs/REPOSITORY_FINAL_STRUCTURE.md` — struttura finale e cosa tenere/archiviare.
- `docs/FIORELLIA_TRAINING_GUIDE.md` — guida semplice al training.
- `docs/FIORELLIA_EVAL_GUIDE.md` — guida semplice alla valutazione.
- `docs/LOCAL_GITHUB_SYNC.md` — come aggiornare locale e GitHub.
- `docs/RELEASE_CHECKLIST.md` — checklist finale GO-LIVE.
- `docs/PRODUCTION_EXPERIMENTAL.md` — distinzione tra componenti produttive/sperimentali.
- `fiorellia/MODEL_CARD.md` — model card Fiorell.IA con stato reale, limiti e riserve.

---

## Root locale ufficiale

Per lavorare in locale usa sempre:

```text
/Users/itsgennymac/GitHub/regulatory-insight-engine
```

Guida sincronizzazione:

```text
docs/LOCAL_GITHUB_SYNC.md
```

---

## Regole di sicurezza e qualità

Prima di considerare valido un run Fiorell.IA:

1. training completato senza errori;
2. adapter ZIP creato e validato;
3. eval completata;
4. metriche salvate;
5. priority cases non peggiorati;
6. decisione finale prodotta in `final_verdict.md`;
7. nessun artifact pesante o sensibile committato per errore.

---

## Disclaimer

Il progetto non fornisce consulenza legale, contabile o regolamentare. Le risposte devono essere considerate output sperimentali da verificare sempre sulle fonti ufficiali.

License: MIT.
