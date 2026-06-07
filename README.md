# hrms-py

FastAPI service boilerplate.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Development

```bash
uvicorn app.main:app --reload
```

The API exposes:

- `GET /`
- `GET /health`
