#!/bin/bash
cd matching-service
uvicorn app.main:app --host 0.0.0.0 --port $PORT
