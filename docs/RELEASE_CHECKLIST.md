# Checklist finale GO-LIVE

Usa questa checklist prima di considerare conclusa una release del repository.

## A. Repository

- [ ] README root aggiornato e leggibile.
- [ ] `fiorellia/README.md` aggiornato.
- [ ] Guide operative presenti in `docs/`.
- [ ] Path locale ufficiale indicato dove serve.
- [ ] Notebook finali chiaramente identificabili.
- [ ] Notebook vecchi non usati come ingresso principale.
- [ ] Nessun artifact pesante committato.

## B. Training Fiorell.IA

- [ ] Notebook training eseguibile top-to-bottom.
- [ ] Sezione config centrale presente.
- [ ] Preflight GPU/config/dataset presente.
- [ ] Training LoRA usa base model previsto.
- [ ] Export adapter ZIP automatico.
- [ ] ZIP validato.
- [ ] Summary finale salvato.

## C. Eval Fiorell.IA

- [ ] Notebook eval eseguibile top-to-bottom.
- [ ] Preflight adapter/eval set/baseline/system prompt presente.
- [ ] Output JSONL prodotto.
- [ ] CSV comparativo prodotto.
- [ ] Metrics JSON prodotto.
- [ ] `final_verdict.md` prodotto.
- [ ] Priority cases controllati.
- [ ] Decisione GO/NO-GO chiara.

## D. Safety / Abstention

- [ ] Unsupported abstention non degradata.
- [ ] Out-of-scope refusal non degradata.
- [ ] Il modello non inventa fonti.
- [ ] Il modello risponde in italiano formale.
- [ ] Se mancano fonti, il modello si astiene.

## E. Locale + GitHub

- [ ] Locale aggiornato da GitHub.
- [ ] `git status` pulito prima del lavoro.
- [ ] Modifiche controllate con `git diff --stat`.
- [ ] Commit con messaggio chiaro.
- [ ] Push completato.
- [ ] GitHub mostra i file aggiornati.

## F. Decisione finale

La release è pronta solo se tutti i punti critici sono soddisfatti.

Se una voce di training/eval/safety fallisce, la decisione è:

```text
NO-GO
```

Se tutte le voci critiche sono soddisfatte, la decisione è:

```text
GO per demo controllata / packaging successivo
```

Non equivale a produzione regolamentare.
