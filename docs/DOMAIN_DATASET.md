# Domain Dataset (supervised) Docs

Location & schema
- Canonical dataset folder: `backend/eval/`.
- JSON Schema: `backend/eval/supervised_schema.json` — required fields, allowed `example_type`s and provenance fields.

Validator and workflow
1. Add a new example to `backend/eval/supervised_seed.jsonl` (follow `ANNOTATION_GUIDELINES.md`).
2. Run the validator:
```bash
python3 backend/eval/validate_supervised_dataset.py --input backend/eval/supervised_seed.jsonl --output backend/eval/supervised_seed.cleaned.jsonl
```
3. Review `Kept records` summary and the cleaned JSONL. Commit cleaned file and increment dataset version.

Provenance and `expected_sources`
- Each example with grounding should include `expected_sources` values that map to files under `docs/` (use consistent filenames).
- Add missing sources to `docs/` or mark the expected source as `external` with a short note in metadata.
 - To help maintain provenance, use the verifier script which checks `expected_sources` against the local corpus:

```bash
python3 backend/eval/check_expected_sources.py --dataset backend/eval/supervised_seed.cleaned.jsonl --docs-path docs --out backend/eval/reports/expected_sources_report.json
```

	The script prints matched and missing sources and writes a compact JSON report when `--out` is provided.

Deduplication & id management
- Validator deduplicates by content hash and `id` field; prefer stable unique ids (e.g., `bank:ifrs9:case-001`).

Annotation guidelines
- See `backend/eval/ANNOTATION_GUIDELINES.md` for labeling rules, examples, and edge cases.

Versioning and governance
- Keep a `dataset_version` entry in the cleaned JSONL header or maintain `backend/eval/DATASET_VERSION` file.
- Before changing schema or label taxonomy, update `supervised_schema.json` and re-run the validator.

Privacy & legal
- Do not include PII or confidential documents in `docs/` or supervised dataset. Redact or replace with synthetic placeholders.
