# LedgrAPI User Setup Guide

## 🚀 Quick Setup (Run as Root)

Since you're currently logged in as root, run this command to create your admin user:

```bash
chmod +x setup_user.sh
./setup_user.sh
```

## 📋 What This Creates

### Users Created:
- **`ledgrapi_admin`** - Your development/admin user (with sudo access)
- **`ledgrapi`** - Service user for running the application

### Permissions:
- Admin user owns the project directory
- Service user can access project files
- Admin user has sudo access for specific commands only
- Proper file permissions for security

## 🔑 After Running the Script

### 1. Set Password for Admin User
```bash
passwd ledgrapi_admin
```

### 2. Switch to Admin User
```bash
su - ledgrapi_admin
```

### 3. Verify Setup
```bash
# Check you're the right user
whoami  # Should show: ledgrapi_admin

# Check project directory
cd /opt/webwise/ledgrapi
ls -la  # Should show you own the files
```

## 🛠️ Development Workflow

### Start Development Server
```bash
# As ledgrapi_admin user
cd /opt/webwise/ledgrapi
./dev.sh
```

### Manage Production Service
```bash
# Check status
ledgrapi-status

# Restart service
ledgrapi-restart

# View logs
ledgrapi-logs
```

### Database Operations
```bash
# Run migrations
db-migrate

# Create new migration
db-revision "add new feature"
```

## 🔧 Useful Aliases (Auto-installed)

| Alias | Command | Description |
|-------|---------|-------------|
| `ledgrapi` | `cd /opt/webwise/ledgrapi` | Go to project directory |
| `ledgrapi-status` | `sudo systemctl status ledgrapi` | Check service status |
| `ledgrapi-restart` | `sudo systemctl restart ledgrapi` | Restart service |
| `ledgrapi-logs` | `sudo journalctl -u ledgrapi -f` | View service logs |
| `nginx-reload` | `sudo systemctl reload nginx` | Reload Nginx config |
| `db-migrate` | `alembic upgrade head` | Run database migrations |
| `dev-server` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Start dev server |

## 🔒 Security Features

### Sudo Access (Limited)
The admin user can run these commands without password:
- Service management (start/stop/restart ledgrapi)
- Nginx management
- Package installation
- Firewall configuration
- SSL certificate management

### File Permissions
- Project files: `ledgrapi_admin:ledgrapi` (775)
- Logs: `ledgrapi_admin:ledgrapi` (775)
- SSH keys: `ledgrapi_admin:ledgrapi_admin` (700)

## 🚨 Important Security Notes

### 1. SSH Key Setup
Add your SSH public key to the admin user:
```bash
# Copy your public key to the server
ssh-copy-id ledgrapi_admin@your-server-ip

# Or manually add to:
nano /home/ledgrapi_admin/.ssh/authorized_keys
```

### 2. Disable Root SSH (Recommended)
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Add/modify these lines:
PermitRootLogin no
PasswordAuthentication no  # If using SSH keys

# Restart SSH
sudo systemctl restart sshd
```

### 3. Firewall Configuration
The script automatically configures UFW:
- SSH (port 22)
- HTTP (port 80)
- HTTPS (port 443)
- Development (port 8000)

## 🐛 Troubleshooting

### Permission Issues
```bash
# Fix ownership
sudo chown -R ledgrapi_admin:ledgrapi /opt/webwise/ledgrapi

# Fix permissions
sudo chmod -R 775 /opt/webwise/ledgrapi
```

### Service Issues
```bash
# Check service status
sudo systemctl status ledgrapi

# View detailed logs
sudo journalctl -u ledgrapi -n 50

# Check Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Database Issues
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Connect to database
sudo -u postgres psql -d ledgrapi_db
```

## 📝 Environment Configuration

### Edit Environment File
```bash
cd /opt/webwise/ledgrapi
nano .env
```

### Key Settings to Configure:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://ledgrapi_user:your_password@localhost/ledgrapi_db

# Security
SECRET_KEY=your-super-secret-key-change-this

# Blockchain (optional)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/your-project-id
POLYGON_RPC_URL=https://polygon-rpc.com

# Payments (optional)
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

## 🎯 Next Steps

1. **Set up your domain** and configure SSL
2. **Configure payment providers** (Stripe, Coinbase Commerce)
3. **Set up monitoring** and backups
4. **Configure Quant integration** when access is granted
5. **Set up CI/CD** for automated deployments

## 🆘 Need Help?

If you encounter issues:
1. Check the logs: `ledgrapi-logs`
2. Verify permissions: `ls -la /opt/webwise/ledgrapi`
3. Test the service: `curl http://localhost:8000/health`
4. Check system resources: `htop`, `df -h`

---

**🎉 You're now ready to develop LedgrAPI as a proper user instead of root!** 