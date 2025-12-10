# SatispayFlow - Project Structure

## Overview
This is a clean, production-ready FastAPI application for automated Deal-to-Order attribution.

## Directory Structure

```
satispayFlow/
├── .git/                    # Git repository
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── PROJECT_STRUCTURE.md    # This file
└── matching-service/       # Main application directory
    ├── app/                # Application code
    │   ├── __init__.py     # Package initializer
    │   ├── main.py         # FastAPI application & endpoints
    │   ├── matching_engine.py  # Core matching logic
    │   └── models.py       # Pydantic data models
    ├── Procfile            # Render deployment configuration
    ├── requirements.txt    # Python dependencies
    └── venv/              # Virtual environment (ignored by git)
```

## Key Files

### Application Code (`matching-service/app/`)
- **main.py**: FastAPI application with all REST endpoints
- **matching_engine.py**: Core business logic for deal-to-order matching
- **models.py**: Pydantic models for request/response validation

### Configuration Files
- **requirements.txt**: Python package dependencies
- **Procfile**: Deployment configuration for Render
- **.gitignore**: Files and directories excluded from version control

## What's NOT Included (Intentionally)
- Test files (test_*.py)
- Test data files (test_payload.json, data/)
- Documentation drafts (docs/)
- Empty directories (n8n/, tests/)
- Virtual environment files (venv/ - excluded via .gitignore)
- Python cache files (__pycache__/ - excluded via .gitignore)

## Deployment
The application is deployed on Render at: https://satispayflow.onrender.com

## Local Development
See README.md for setup instructions.
