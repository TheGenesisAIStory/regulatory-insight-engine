# Guida semplice — Training Fiorell.IA

Questa guida spiega come addestrare l’adapter LoRA di Fiorell.IA usando Google Colab.

Non serve usare il terminale. Devi solo aprire il notebook e cliccare Play sulle celle.

## Notebook da aprire

```text
fiorellia/training/01_start_here_training_export.ipynb
```

## Prima di iniziare

Controlla di avere:

1. un account Google;
2. Google Drive disponibile;
3. runtime Colab Pro con GPU A100;
4. repository clonato o accessibile nel notebook;
5. dataset training presente:

```text
fiorellia/training/supervised_v1_curated_20260421.jsonl
```

6. config presente:

```text
fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

## Cosa devi fare

### Passo 1 — Apri Colab

Apri il notebook e scegli:

```text
Runtime > Change runtime type > A100 GPU
```

### Passo 2 — Esegui le celle dall’alto verso il basso

Non saltare celle.

Quando una cella termina correttamente, prosegui con quella successiva.

### Passo 3 — Controlla il preflight

Il notebook deve confermare:

- GPU disponibile;
- config trovata;
- dataset trovato;
- output directory pronta;
- base model corretto.

Se manca la GPU, Colab mostrerà un errore leggibile. In quel caso cambia runtime e riparti.

### Passo 4 — Avvia training

Il notebook lancia lo script di training esistente. Non devi modificare codice Python.

Attendi la fine del training.

### Passo 5 — Export adapter

A fine training il notebook crea lo ZIP dell’adapter.

Output atteso:

```text
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip
```

### Passo 6 — Conclusione finale

L’ultima cella produce:

```text
training_summary.json
training_final_summary.md
```

Leggi il messaggio finale.

## Output attesi

```text
fiorellia_lora_adapter.zip
training_summary.json
training_final_summary.md
```

## Se qualcosa fallisce

### Errore: GPU non disponibile

Soluzione:

```text
Runtime > Change runtime type > A100 GPU
```

Poi riesegui il notebook dall’inizio.

### Errore: dataset non trovato

Controlla che esista:

```text
fiorellia/training/supervised_v1_curated_20260421.jsonl
```

### Errore: config non trovata

Controlla che esista:

```text
fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

### Errore: adapter ZIP incompleto

Significa che il training non ha prodotto tutti i file necessari. Controlla se nella cartella output esistono:

```text
adapter_config.json
adapter_model.safetensors
```

## Regola importante

Non modificare il modello base, la logica LoRA o il comportamento di astensione senza una nuova valutazione completa.
