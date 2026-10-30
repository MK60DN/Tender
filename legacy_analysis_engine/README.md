# Legacy Analysis Engine Archive

This directory preserves the source snapshot that existed on the remote `main` branch at commit `5e3a191d59a759596ef19ef1e5d5b3948369a600` on 2026-10-31.

It is retained because the remote branch and the full local release history had no common ancestor, and the remote snapshot contained files absent from the local repository. The files cover an experimental group emotion-cognition engine: emotion vectorization, topology analysis, causal analysis, cognition state, fusion, strategy and heterogeneity coordination.

The complete remote snapshot is preserved under `upstream_snapshot/`. The extracted folders beside it provide a compact view of the source engine and its provenance files.

## Status and boundaries

- This archive is **not** part of the current Tender runtime, package, test baseline, teaching site or supported product surface.
- The upstream snapshot is incomplete: some tests reference modules that are not present in the snapshot.
- Parts of the snapshot contain syntax damage introduced before this archive was created.
- No file here is evidence of validated educational, clinical or commercial capability.
- The current supported system remains under `agent_layer/`, `site/` and `docs/`.

## Provenance files

- `upstream-pyproject.toml`: the upstream packaging metadata as received.
- `upstream-requirements.txt`: the upstream dependency list as received.
- `upstream.gitignore`: the upstream ignore rules as received.
- `docs/source_framework_architecture.md`: the upstream architecture document.

The archive is preserved for provenance and possible future recovery. It must not be imported by default or presented as a finished engine.