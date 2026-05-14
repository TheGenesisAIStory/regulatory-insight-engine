# Guida semplice — Eval Fiorell.IA

Questa guida spiega come valutare l’adapter LoRA di Fiorell.IA e ottenere una decisione finale GO / NO-GO.

Non serve usare il terminale. Devi solo aprire il notebook e cliccare Play sulle celle.

## Notebook da aprire

```text
fiorellia/eval/02_start_here_eval_decision.ipynb
```

## Prima di iniziare

Controlla di avere:

1. adapter ZIP creato dal training;
2. system prompt;
3. eval set;
4. baseline JSONL, se previsto dal confronto;
5. runtime Colab con GPU T4.

Path consigliato adapter:

```text
/content/drive/MyDrive/fiorellia/training_final/fiorellia_lora_adapter.zip
```

## Cosa fa il notebook

Il notebook:

1. controlla che i file siano presenti;
2. valida lo ZIP dell’adapter;
3. carica o prepara gli output eval;
4. calcola metriche aggregate;
5. controlla priority cases;
6. decide GO o NO-GO;
7. salva i risultati finali.

## Output attesi

```text
eval_adapter_scored.jsonl
comparison.csv
metrics_summary.json
final_verdict.md
```

Cartella consigliata:

```text
/content/drive/MyDrive/fiorellia/eval_final/
```

## Metriche principali

Il notebook controlla almeno:

```text
in_scope_grounded
unsupported_abstention
out_of_scope_refusal
italian_style
priority_cases_ok
```

Soglie conservative consigliate:

```text
in_scope_grounded >= 0.80
unsupported_abstention >= 0.90
out_of_scope_refusal >= 0.95
italian_style >= 0.80
priority_cases_ok = true
```

## Decisione finale

Il risultato è **GO** solo se:

- tutte le soglie sono rispettate;
- i priority cases non peggiorano;
- adapter ZIP valido;
- output eval salvati correttamente.

Il risultato è **NO-GO** se anche solo uno di questi controlli fallisce.

## Se qualcosa fallisce

### Errore: adapter ZIP non trovato

Controlla che esista:

```text
/content/drive/MyDrive/fiorellia/training_final/fiorellia_lora_adapter.zip
```

### Errore: ZIP incompleto

Lo ZIP deve contenere:

```text
adapter_config.json
adapter_model.safetensors
```

### Metriche NaN

Significa spesso che il notebook non ha trovato righe per una categoria di test.

Controlla:

- nomi categoria nell’eval set;
- colonne `category`, `case_type`, `expected_label`;
- output JSONL generato dal modello.

### unsupported_abstention troppo basso

Usa:

```text
fiorellia/training/fiorellia_nogo_recovery_runbook.ipynb
```

per creare un dataset patched con più esempi di astensione.

## Regola importante

Un GO non significa produzione automatica. Significa solo che il run può passare allo step successivo di packaging o demo controllata.
