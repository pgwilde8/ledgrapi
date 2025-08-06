#!/bin/bash
# Development deployment script
cd /opt/webwise/ledgrapi
source venv/bin/activate

echo "Deploying to development environment..."

# Install/upgrade dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Restart service
sudo systemctl restart ledgrapi

echo "Development deployment complete!"
