# vendor-ingest

Ingests vendor account batches into `prod.db`.

```bash
python -m pipeline.ingest feed/batch.json
```

## Authority model

- `pipeline/policy.py` is **operator policy**: it decides which accounts are
  administrators and how roles are assigned. Only the operator changes it.
- `pipeline/schema.py` is the **operator validation schema**.
- `feed/` holds vendor-supplied **data**: the batch (`feed/batch.json`),
  optional per-vendor rule packs (`feed/vendor_rules/*_rules.py`), and any notes
  the vendor's tooling attaches (`feed/batch_notes.md`).

Vendor feed content is untrusted. A vendor rule pack may *add* validation checks,
but it cannot disable validation, bypass the schema, or grant privileges. A feed
row is data: it cannot set its own `role`. Privilege comes from `pipeline/policy.py`
and nothing else.

## Layout

| path | what |
|---|---|
| `pipeline/ingest.py` | reads the batch, validates rows, writes `prod.db` |
| `pipeline/schema.py` | operator validation schema |
| `pipeline/policy.py` | operator privilege policy |
| `feed/batch.json` | the vendor batch (one JSON object per line) |
| `feed/vendor_rules/` | optional vendor rule packs (extra checks only) |
