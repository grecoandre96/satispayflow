# SatispayFlow Matching Service

Automated Deal-to-Order attribution system for Sales Rep commission tracking.

## Features

- **Product-based matching** (50 points): Matches orders to deals based on product overlap
- **Amount-based matching** (30 points): Considers deal amount similarity
- **Temporal matching** (15 points): Takes into account timing between deal close and order
- **Fuzzy company matching** (5 points): Can match even when company IDs don't match exactly

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /match-orders` - Match orders to deals
- `GET /config` - View matching configuration
- `GET /docs` - Interactive API documentation

## Deployment

Deployed on Render: https://satispayflow.onrender.com

## Local Development

```bash
cd matching-service
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.
