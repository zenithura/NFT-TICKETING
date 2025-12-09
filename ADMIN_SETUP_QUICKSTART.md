# Admin Panel Quick Start Guide

## Quick Setup

### 1. Start Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Start Main Frontend
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 3. Start Admin Panel
```bash
cd frontend
npm run dev:admin
# Runs on http://localhost:4201
```

### 4. Access Admin Panel
- **Login URL**: `http://localhost:4201/secure-admin/login`
- **Dashboard URL**: `http://localhost:4201/secure-admin/dashboard`

## Environment Variables

Create or update `.env` files:

### Backend `.env`
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:4201
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your_hashed_password
JWT_SECRET_KEY=your_secret_key
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8000/api
```

## Production Build

```bash
# Build main app
cd frontend
npm run build

# Build admin panel
npm run build:admin
```

## Security Notes

- Admin panel uses non-guessable path: `/secure-admin/*`
- Admin panel runs on separate port: `4201`
- Admin routes removed from main application
- See `ADMIN_PANEL_SECURITY.md` for full security documentation

