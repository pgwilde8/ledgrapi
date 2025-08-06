#!/bin/bash
# Development server script
cd /opt/webwise/ledgrapi
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
