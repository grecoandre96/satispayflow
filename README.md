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

## Usage Example

### Using the deployed API

```bash
curl -X POST https://satispayflow.onrender.com/match-orders \
  -H "Content-Type: application/json" \
  -d @example_payload.json
```

### Using PowerShell (Windows)

```powershell
$body = Get-Content example_payload.json -Raw
Invoke-RestMethod -Uri "https://satispayflow.onrender.com/match-orders" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### Expected Response

```json
{
  "attributions": [
    {
      "order_id": "order_001",
      "matched_deal_id": "DEAL-001",
      "sales_rep_id": "rep_001",
      "sales_rep_name": "John Doe",
      "confidence_score": 95.5,
      "match_details": {
        "product_score": 50.0,
        "amount_score": 30.0,
        "temporal_score": 10.5,
        "company_score": 5.0
      }
    }
  ],
  "unmatched_orders": []
}
```

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information about the codebase organization.

