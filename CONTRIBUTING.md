# Contributing

## Scope

This repository accepts contributions to whitepapers, research reports, experiments, knowledge databases and reference modeling code. Product UI, application runtime and deployment changes belong in https://github.com/MK60DN/Tender-Product.

## Setup

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements-research.txt
    python scripts/verify_research.py

## Rules

1. Do not commit real learner, family, health, beneficiary or institution-identifiable data.
2. Label synthetic fixtures explicitly.
3. Every behavioral or educational claim needs a source, uncertainty and failure boundary.
4. New model code should include a deterministic test or a reproducible experiment.
5. Distinguish implemented models, target architecture and research hypotheses.
6. Update the relevant whitepaper or research report when claim boundaries change.
7. Use a pull request description that states the question, change, evidence and limitations.

## Pull requests

Describe:

- research question;
- change;
- data source and sample;
- test or reproduction command;
- privacy impact;
- unsupported claims or known gaps.

## License of contributions

By contributing, you agree that your contribution is distributed under the PolyForm Noncommercial License 1.0.0. Commercial use requires separate written permission.
