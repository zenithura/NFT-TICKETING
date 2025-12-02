# 🚀 Complete Project Startup Guide

## Overview

This guide will help you start the entire NFT Ticketing Platform with frontend, backend, and database.

## Prerequisites

- ✅ Python 3.8+
- ✅ Node.js 16+
- ✅ Supabase account (free tier works)
- ✅ Database schema executed in Supabase

## Step-by-Step Setup

### 1️⃣ Database Setup (Supabase)

1. **Create Supabase Project:**
   - Go to https://supabase.com
   - Create a new project
   - Wait for project to be ready (~2 minutes)

2. **Run Database Schema:**
   - Open Supabase SQL Editor
   - Copy contents of `backend/complete_database_schema.sql`
   - Paste and run in SQL Editor
   - Verify tables were created

3. **Get Supabase Credentials:**
   - Go to **Settings** → **API**
   - Copy:
     - Project URL → `SUPABASE_URL`
     - anon public key → `SUPABASE_KEY`
     - service_role key → `SUPABASE_SERVICE_KEY`

### 2️⃣ Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF

# Edit .env file and add your Supabase credentials
nano .env  # or use your preferred editor

# Start backend server
python main.py
```

**Or use the startup script:**
```bash
cd backend
chmod +x start_backend.sh
./start_backend.sh
```

**Verify backend is running:**
- Open: http://localhost:8000/health
- Should see: `{"status":"healthy"}`
- API Docs: http://localhost:8000/docs

### 3️⃣ Frontend Setup

**Open a NEW terminal window:**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Verify frontend is running:**
- Open: http://localhost:5173
- Should see the NFT Ticketing Platform homepage

### 4️⃣ Test the Application

1. **Open Frontend:** http://localhost:5173
2. **Click "Register"** or navigate to `/register`
3. **Fill in registration form:**
   - Email: `test@example.com`
   - Password: `TestPass123!`
   - Select role: **Buyer** or **Organizer**
   - Click "Create Account"
4. **Verify:** You should be redirected to dashboard

## 🎯 Quick Commands Reference

### Start Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
python main.py
```

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Test Registration API
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "role": "BUYER"
  }'
```

## 🔧 Common Issues & Solutions

### Backend: "Connection refused"
**Problem:** Backend server not running  
**Solution:**
```bash
cd backend
source venv/bin/activate
python main.py
```

### Backend: "Module not found"
**Problem:** Dependencies not installed  
**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Backend: "Supabase connection error"
**Problem:** Missing or incorrect Supabase credentials  
**Solution:** Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Frontend: "ERR_CONNECTION_REFUSED"
**Problem:** Backend not running or wrong URL  
**Solution:**
1. Make sure backend is running on port 8000
2. Check `frontend/.env` has: `VITE_API_URL=http://localhost:8000/api`

### Database: "Table does not exist"
**Problem:** Database schema not run  
**Solution:** Run `backend/complete_database_schema.sql` in Supabase SQL Editor

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |

## ✅ Verification Checklist

Before testing, verify:

- [ ] Supabase project created
- [ ] Database schema executed successfully
- [ ] Backend `.env` file configured with Supabase credentials
- [ ] Backend dependencies installed
- [ ] Backend server running (check http://localhost:8000/health)
- [ ] Frontend dependencies installed
- [ ] Frontend server running (check http://localhost:5173)
- [ ] Can access registration page
- [ ] Can submit registration form

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Backend health check returns `{"status":"healthy"}`
2. ✅ Frontend loads at http://localhost:5173
3. ✅ Registration form submits successfully
4. ✅ User is redirected to dashboard after registration
5. ✅ No console errors in browser
6. ✅ No errors in backend terminal

## 📚 Additional Resources

- **Backend Setup**: `backend/QUICK_START.md`
- **Backend API Docs**: http://localhost:8000/docs (when running)
- **Database Schema**: `backend/complete_database_schema.sql`
- **Supabase Setup**: `SUPABASE_AUTH_SETUP.md`

## 🆘 Need Help?

1. Check backend logs in terminal
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Ensure database schema is executed
5. Check that ports 8000 and 5173 are not in use

