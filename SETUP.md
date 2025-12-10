# Setup Instructions for Reviewers

## Quick Start

This project is already deployed and running at: **https://satispayflow.onrender.com**

You can test it immediately without any local setup!

## Testing the Deployed API

### Option 1: Using the Interactive Documentation (Recommended)
1. Visit https://satispayflow.onrender.com/docs
2. Click on the `POST /match-orders` endpoint
3. Click "Try it out"
4. Use the example payload below or modify it
5. Click "Execute"

### Option 2: Using curl (Linux/Mac/Git Bash)
```bash
curl -X POST https://satispayflow.onrender.com/match-orders \
  -H "Content-Type: application/json" \
  -d @example_payload.json
```

### Option 3: Using PowerShell (Windows)
```powershell
$body = Get-Content example_payload.json -Raw
Invoke-RestMethod -Uri "https://satispayflow.onrender.com/match-orders" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## Local Development Setup (Optional)

If you want to run the application locally:

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation Steps

1. **Navigate to the application directory**
   ```bash
   cd matching-service
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information about the codebase organization.

## Key Features

- **Product-based matching** (50 points): Primary matching criterion
- **Amount-based matching** (30 points): Considers deal value similarity
- **Temporal matching** (15 points): Time-based relevance
- **Fuzzy company matching** (5 points): Handles company name variations

## API Endpoints

- `GET /` - API information and welcome message
- `GET /health` - Health check endpoint
- `POST /match-orders` - Main matching endpoint (see docs for payload structure)
- `GET /config` - View current matching configuration
- `GET /docs` - Interactive Swagger UI documentation

## Example Payload

The file `example_payload.json` contains a sample request that demonstrates:
- Company data structure
- Deal information with products
- Order data to be matched
- Expected matching behavior

## Support

For questions or issues, please refer to:
- **README.md** - General project overview
- **PROJECT_STRUCTURE.md** - Codebase organization
- **Interactive Docs** - API endpoint details and testing interface

---

**Note**: The deployed version on Render may take 30-60 seconds to wake up on the first request if it has been idle (free tier limitation).
