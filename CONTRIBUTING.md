# Contributing

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements-dev.txt
python agent_layer/tests/run_all.py
```

## Rules

1. Do not commit `.env`, session secrets, tenant databases or real learner data.
2. Every behavioral claim must have a source, uncertainty and a failure boundary.
3. Language evidence must not update mastery by itself.
4. High-risk signals must retain a deterministic human-escalation path.
5. New endpoints need tests and documentation.
6. Research fixtures must be clearly labeled synthetic.
7. Run the full test suite before opening a pull request.

## Pull requests

Describe:
- user problem;
- change;
- evidence or test;
- privacy/security impact;
- unsupported claims or known gaps.

Use the PR template in `.github/pull_request_template.md`.

## License of contributions

By contributing, you agree that your contribution may be distributed under the project's PolyForm Noncommercial License 1.0.0. Commercial licensing requires separate permission from the copyright holder.
