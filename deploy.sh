#!/bin/bash

# LedgrAPI Deployment Script
# This script sets up LedgrAPI on a production server

set -e

echo "🚀 Starting LedgrAPI deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/webwise/ledgrapi"
SERVICE_USER="ledgrapi"
SERVICE_GROUP="ledgrapi"
PYTHON_VERSION="3.11"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory $PROJECT_DIR does not exist"
    exit 1
fi

cd "$PROJECT_DIR"

print_status "Installing system dependencies..."

# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    build-essential \
    libpq-dev \
    curl \
    git

print_status "Creating service user..."

# Create service user if it doesn't exist
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d "$PROJECT_DIR" "$SERVICE_USER"
    sudo usermod -aG sudo "$SERVICE_USER"
fi

# Set ownership
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"

print_status "Setting up Python virtual environment..."

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

print_status "Setting up PostgreSQL database..."

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ledgrapi_db;
CREATE USER ledgrapi_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ledgrapi_db TO ledgrapi_user;
ALTER USER ledgrapi_user CREATEDB;
\q
EOF

print_status "Setting up environment configuration..."

# Copy environment file
if [ ! -f ".env" ]; then
    cp env.example .env
    print_warning "Please edit .env file with your actual configuration values"
fi

print_status "Setting up database migrations..."

# Initialize Alembic
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head

print_status "Setting up systemd service..."

# Copy systemd service file
sudo cp systemd/ledgrapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ledgrapi

print_status "Setting up Nginx..."

# Copy Nginx configuration
sudo cp nginx/ledgrapi.conf /etc/nginx/sites-available/ledgrapi
sudo ln -sf /etc/nginx/sites-available/ledgrapi /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

print_status "Setting up SSL certificate..."

# Get SSL certificate (uncomment when domain is ready)
# sudo certbot --nginx -d ledgrapi.com -d www.ledgrapi.com --non-interactive --agree-tos --email your-email@example.com

print_status "Creating log directories..."

# Create log directories
mkdir -p logs
sudo mkdir -p /var/log/ledgrapi
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" /var/log/ledgrapi

print_status "Setting up static files..."

# Create static directory
mkdir -p app/static

print_status "Starting services..."

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Start LedgrAPI
sudo systemctl start ledgrapi

print_status "Checking service status..."

# Check service status
sudo systemctl status ledgrapi --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status postgresql --no-pager
sudo systemctl status redis-server --no-pager

print_status "Testing application..."

# Wait a moment for the application to start
sleep 5

# Test health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Application is running successfully!"
else
    print_error "Application failed to start. Check logs with: sudo journalctl -u ledgrapi -f"
fi

print_status "Deployment completed!"

echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual configuration values"
echo "2. Set up SSL certificate: sudo certbot --nginx -d ledgrapi.com"
echo "3. Configure firewall: sudo ufw allow 80,443"
echo "4. Set up monitoring and backups"
echo "5. Test the API at: http://localhost:8000/api/docs"
echo ""
echo "🔧 Useful commands:"
echo "  View logs: sudo journalctl -u ledgrapi -f"
echo "  Restart service: sudo systemctl restart ledgrapi"
echo "  Check status: sudo systemctl status ledgrapi"
echo "  View Nginx logs: sudo tail -f /var/log/nginx/ledgrapi_access.log"
echo ""
echo "🎉 LedgrAPI is now deployed and running!" 