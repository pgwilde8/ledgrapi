# LedgrAPI - Quant-Powered Web3 API Monetization Platform

> RapidAPI meets Stripe — but for cross-chain, trustless, programmable APIs

## 🧠 Project Vision

LedgrAPI is a **Quant-powered Web3 API monetization platform** that enables developers to:
- Publish APIs (messaging, data, DeFi, identity, etc.)
- Gate access using **QNT**, **USDC**, or **NFTs**
- Enable smart **cross-chain messaging** (Quant-style)
- Monetize endpoints through usage-based pricing
- Route tx/data across chains using **Quant Overledger**

## 🏗️ Architecture

```
ledgrapi/
├── app/                    # Main application code
│   ├── api/               # API routes
│   ├── core/              # Core configuration and utilities
│   ├── db/                # Database models and session
│   ├── services/          # Business logic services
│   ├── templates/         # Jinja2 HTML templates
│   └── utils/             # Utility functions
├── migrations/            # Database migrations
├── tests/                 # Test suite
├── docker/                # Docker configuration
├── nginx/                 # Nginx configuration
└── systemd/               # Systemd service files
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis (for Celery)
- Node.js (for frontend assets)

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository>
cd ledgrapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment configuration:**
```bash
cp .env.example .env
# Edit .env with your database, API keys, and blockchain settings
```

3. **Database setup:**
```bash
alembic upgrade head
```

4. **Run development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Production Deployment

### Systemd Service
```bash
sudo cp systemd/ledgrapi.service /etc/systemd/system/
sudo systemctl enable ledgrapi
sudo systemctl start ledgrapi
```

### Nginx Configuration
```bash
sudo cp nginx/ledgrapi.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/ledgrapi.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### SSL Certificate
```bash
sudo certbot --nginx -d ledgrapi.com -d www.ledgrapi.com
```

## 📊 API Endpoints

### Core API Routes
- `POST /api/v1/publish-api` - Register a new API
- `POST /api/v1/call-api` - Access a registered API
- `GET /api/v1/apis` - List available APIs
- `GET /api/v1/usage` - Get usage statistics

### Authentication
- `POST /api/v1/auth/register` - Developer registration
- `POST /api/v1/auth/login` - Developer login
- `POST /api/v1/auth/wallet` - Wallet-based authentication

### Billing & Payments
- `POST /api/v1/billing/create-subscription` - Create subscription
- `GET /api/v1/billing/usage` - Get billing usage
- `POST /api/v1/billing/webhook` - Payment webhooks

## 💰 Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 1 API, 1,000 calls/month, testnet only |
| **Builder** | $49/mo | 10k calls, 3 APIs, QNT/USDC accepted |
| **Pro** | $199/mo | 100k calls, NFT-based access, logs, SLAs |
| **Enterprise** | $1,000+/mo | Custom integrations, chain SLAs, Quant routing |

## 🔐 Security

- API key authentication
- Rate limiting per tier
- CORS configuration
- SSL/TLS encryption
- Database encryption for sensitive data
- Audit logging for all API calls

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

## 📝 License

Proprietary - All rights reserved

## 🤝 Contributing

This is a private project. For support or questions, contact the development team. 