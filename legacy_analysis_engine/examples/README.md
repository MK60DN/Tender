# Examples

Start the application first:

```bash
cd agent_layer
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Then run:

```bash
python examples/api_smoke.py
```
