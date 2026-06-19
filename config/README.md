# Configuration

`project_config.yaml` controls how the notebooks run.

## Default Cached Reproduction

Use these settings to reproduce figures, tables, and summary artifacts from the cached data included in the repository:

```yaml
run_mode: fast
inputs:
  allow_network: false
  use_existing_data: true
outputs:
  overwrite_data: false
  overwrite_artifacts: true
```

Meaning:

- `run_mode: fast`: use cached data and refresh outputs.
- `inputs.allow_network: false`: do not fetch new remote data.
- `inputs.use_existing_data: true`: read the included parquet/csv files.
- `outputs.overwrite_data: false`: do not rewrite prepared data files.
- `outputs.overwrite_artifacts: true`: regenerate figures, tables, and summary files.

## Optional Fetch/Test Settings

These are not needed for cached reproduction.

- `openalex.sample_limit`: leave blank for no OpenAlex sampling. Set a small number only when testing raw OpenAlex fetch notebooks.
- `openalex.sample_include_work_ids`: optional OpenAlex work IDs to force into a sampled fetch.
- `openalex.fetch_workers: 8`: parallel workers for OpenAlex fetching if network mode is enabled.
- `external_validation.sample_limit`: leave blank to validate all researchers. Set a small number only when testing ORCID/Researchr validation.
- `external_validation.max_dois_per_researcher`: leave blank to check all available DOIs per researcher.

For cached reproduction, no OpenAlex API key is needed. If network fetching is enabled later, copy `key.env.example` to `key.env` and add an OpenAlex key.
