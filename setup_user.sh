#!/bin/bash

# LedgrAPI User Setup Script
# Creates a proper admin user for development and deployment

set -e

echo "🔧 Setting up LedgrAPI admin user..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/webwise/ledgrapi"
ADMIN_USER="ledgrapi_admin"
SERVICE_USER="ledgrapi"
SERVICE_GROUP="ledgrapi"

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
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

print_status "Creating admin user: $ADMIN_USER"

# Create admin user
if ! id "$ADMIN_USER" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo "$ADMIN_USER"
    print_status "User $ADMIN_USER created successfully"
else
    print_warning "User $ADMIN_USER already exists"
fi

# Create service user if it doesn't exist
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$PROJECT_DIR" "$SERVICE_USER"
    print_status "Service user $SERVICE_USER created"
else
    print_warning "Service user $SERVICE_USER already exists"
fi

# Create service group
if ! getent group "$SERVICE_GROUP" > /dev/null 2>&1; then
    groupadd "$SERVICE_GROUP"
    print_status "Service group $SERVICE_GROUP created"
fi

# Add admin user to service group
usermod -a -G "$SERVICE_GROUP" "$ADMIN_USER"

print_status "Setting up project directory permissions..."

# Create project directory if it doesn't exist
mkdir -p "$PROJECT_DIR"

# Set ownership: admin user owns the project, service user can access
chown -R "$ADMIN_USER:$SERVICE_GROUP" "$PROJECT_DIR"
chmod -R 775 "$PROJECT_DIR"

# Create log directories
mkdir -p "$PROJECT_DIR/logs"
mkdir -p /var/log/ledgrapi
chown -R "$ADMIN_USER:$SERVICE_GROUP" "$PROJECT_DIR/logs"
chown -R "$ADMIN_USER:$SERVICE_GROUP" /var/log/ledgrapi

print_status "Setting up sudo access..."

# Create sudoers file for the admin user
cat > /etc/sudoers.d/ledgrapi_admin << EOF
# LedgrAPI Admin User Sudo Access
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start ledgrapi
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop ledgrapi
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart ledgrapi
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl status ledgrapi
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u ledgrapi *
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/nginx -t
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload nginx
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/certbot *
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/apt update
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/apt install *
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/apt upgrade
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/ufw *
$ADMIN_USER ALL=(ALL) NOPASSWD: /usr/bin/su - $SERVICE_USER
EOF

chmod 440 /etc/sudoers.d/ledgrapi_admin

print_status "Setting up SSH access..."

# Create .ssh directory for admin user
mkdir -p /home/$ADMIN_USER/.ssh
chown -R $ADMIN_USER:$ADMIN_USER /home/$ADMIN_USER/.ssh
chmod 700 /home/$ADMIN_USER/.ssh

# Create authorized_keys file
touch /home/$ADMIN_USER/.ssh/authorized_keys
chown $ADMIN_USER:$ADMIN_USER /home/$ADMIN_USER/.ssh/authorized_keys
chmod 600 /home/$ADMIN_USER/.ssh/authorized_keys

print_status "Setting up development environment..."

# Switch to admin user and set up Python environment
su - $ADMIN_USER << 'EOF'
cd /opt/webwise/ledgrapi

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create development environment file
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "Development environment file created. Please edit .env with your settings."
fi

# Create useful aliases
cat >> ~/.bashrc << 'BASH_ALIASES'

# LedgrAPI Development Aliases
alias ledgrapi='cd /opt/webwise/ledgrapi'
alias ledgrapi-logs='sudo journalctl -u ledgrapi -f'
alias ledgrapi-status='sudo systemctl status ledgrapi'
alias ledgrapi-restart='sudo systemctl restart ledgrapi'
alias ledgrapi-stop='sudo systemctl stop ledgrapi'
alias ledgrapi-start='sudo systemctl start ledgrapi'
alias nginx-reload='sudo systemctl reload nginx'
alias nginx-status='sudo systemctl status nginx'
alias db-migrate='alembic upgrade head'
alias db-revision='alembic revision --autogenerate -m'
alias dev-server='uvicorn app.main:app --reload --host 0.0.0.0 --port 9176'
BASH_ALIASES

echo "Development environment setup complete!"
EOF

print_status "Setting up Git configuration..."

# Configure Git for the admin user
su - $ADMIN_USER << 'EOF'
git config --global user.name "LedgrAPI Admin"
git config --global user.email "admin@ledgrapi.com"
git config --global init.defaultBranch main
EOF

print_status "Creating useful scripts..."

# Create development helper scripts
cat > /opt/webwise/ledgrapi/dev.sh << 'EOF'
#!/bin/bash
# Development server script
cd /opt/webwise/ledgrapi
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 9176
EOF

cat > /opt/webwise/ledgrapi/deploy-dev.sh << 'EOF'
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
EOF

chmod +x /opt/webwise/ledgrapi/dev.sh
chmod +x /opt/webwise/ledgrapi/deploy-dev.sh
chown $ADMIN_USER:$SERVICE_GROUP /opt/webwise/ledgrapi/dev.sh
chown $ADMIN_USER:$SERVICE_GROUP /opt/webwise/ledgrapi/deploy-dev.sh

print_status "Setting up firewall rules..."

# Configure UFW firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 9176  # For LedgrAPI development server

print_status "User setup completed successfully!"

echo ""
echo "🎉 LedgrAPI Admin User Setup Complete!"
echo ""
echo "📋 User Information:"
echo "  Admin User: $ADMIN_USER"
echo "  Service User: $SERVICE_USER"
echo "  Project Directory: $PROJECT_DIR"
echo ""
echo "🔑 Next Steps:"
echo "1. Set a password for the admin user:"
echo "   passwd $ADMIN_USER"
echo ""
echo "2. Switch to the admin user:"
echo "   su - $ADMIN_USER"
echo ""
echo "3. Edit the environment file:"
echo "   cd /opt/webwise/ledgrapi && nano .env"
echo ""
echo "4. Start development:"
echo "   ./dev.sh"
echo ""
echo "🔧 Useful Commands (as admin user):"
echo "  ledgrapi-status    - Check service status"
echo "  ledgrapi-restart   - Restart the service"
echo "  ledgrapi-logs      - View service logs"
echo "  dev-server         - Start development server"
echo "  db-migrate         - Run database migrations"
echo ""
echo "⚠️  Security Notes:"
echo "- The admin user has sudo access for specific commands only"
echo "- SSH keys should be added to /home/$ADMIN_USER/.ssh/authorized_keys"
echo "- Consider disabling password authentication for SSH"
echo ""
echo "🚀 You're now ready to develop LedgrAPI as a proper user!" 