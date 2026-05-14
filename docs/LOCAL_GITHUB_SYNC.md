# Guida semplice — Aggiornare locale e GitHub

Questa guida usa sempre la root locale ufficiale:

```text
/Users/itsgennymac/Documents/GitHub/regulatory-insight-engine
```

## Obiettivo

Tenere allineati:

- repository locale sul Mac;
- repository GitHub;
- notebook e documentazione finali.

## Passo 1 — Apri il terminale nella cartella corretta

```bash
cd '/Users/itsgennymac/Documents/GitHub/regulatory-insight-engine'
```

## Passo 2 — Controlla lo stato

```bash
git status
```

Se vedi file modificati, controlla che siano file voluti.

## Passo 3 — Aggiorna dal remoto

```bash
git pull origin main
```

Se Git segnala conflitti, non forzare. Risolvi prima i file indicati.

## Passo 4 — Controlla cosa è cambiato

```bash
git status
git diff --stat
```

## Passo 5 — Non committare artifact pesanti

Prima del commit controlla che non ci siano file come:

```text
*.zip
*.safetensors
adapter_model.bin
adapter_model.safetensors
artifacts/
outputs/
```

Se compaiono nello status, rimuovili dallo staging:

```bash
git restore --staged <file>
```

oppure spostali fuori dal repository.

## Passo 6 — Aggiungi solo file sorgente/documentazione

```bash
git add README.md docs/ fiorellia/
```

## Passo 7 — Commit pulito

```bash
git commit -m "Finalize Fiorell.IA user-friendly training and eval workflow"
```

## Passo 8 — Push su GitHub

```bash
git push origin main
```

## Passo 9 — Verifica finale

```bash
git status
```

Output desiderato:

```text
nothing to commit, working tree clean
```

## Se qualcosa va storto

### Errore di autenticazione GitHub

Usa GitHub Desktop oppure aggiorna token/credenziali Git.

### Errore di conflitto

Non fare `git push --force`. Prima esegui:

```bash
git status
```

Apri i file in conflitto, risolvi, poi:

```bash
git add <file-risolto>
git commit
```

### Hai committato per errore un artifact pesante

Se non hai ancora fatto push:

```bash
git reset --soft HEAD~1
git restore --staged <file-pesante>
git commit -m "Finalize Fiorell.IA user-friendly workflow"
```

## Regola finale

GitHub deve contenere codice, notebook, config e guide. Gli output dei run devono restare su Drive o in `artifacts/` locali non versionati.
