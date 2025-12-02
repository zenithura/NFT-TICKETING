# Backend Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file in the `backend/` directory:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# JWT Configuration (auto-generated if not set)
JWT_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Where to find Supabase credentials:**
1. Go to your Supabase project dashboard
2. Click **Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY`

**Generate JWT Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Start the Server

**Option A: Using the startup script (Recommended)**
```bash
cd backend
chmod +x start_backend.sh
./start_backend.sh
```

**Option B: Manual start**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

**Option C: Using uvicorn directly**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## ✅ Verify It's Working

1. **Check health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy"}`

2. **Check API docs:**
   Open browser: http://localhost:8000/docs

3. **Test registration:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123!",
       "role": "BUYER"
     }'
   ```

## 🔧 Troubleshooting

### Issue: "Connection refused"
- **Solution**: Make sure the backend server is running on port 8000
- Check: `lsof -i :8000` (Linux/Mac) or `netstat -ano | findstr :8000` (Windows)

### Issue: "Module not found"
- **Solution**: Make sure virtual environment is activated and dependencies are installed
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

### Issue: "Supabase connection error"
- **Solution**: Check your `.env` file has correct Supabase credentials
- Verify credentials in Supabase dashboard

### Issue: "JWT_SECRET_KEY not set"
- **Solution**: Add JWT_SECRET_KEY to `.env` file
- Generate one: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### Issue: "Port 8000 already in use"
- **Solution**: Kill the process using port 8000 or change port in `main.py`
  ```bash
  # Linux/Mac
  lsof -ti:8000 | xargs kill -9
  
  # Or change port in main.py line 63:
  uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
  ```

## 📋 Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with Supabase credentials
- [ ] Database schema run in Supabase (`complete_database_schema.sql`)
- [ ] Backend server started and running on port 8000

## 🎯 Next Steps

Once backend is running:

1. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Test Full Flow:**
   - Open http://localhost:5173
   - Try registering a new user
   - Try logging in

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Backend Setup Guide**: `BACKEND_SETUP.md`
- **Database Schema**: `complete_database_schema.sql`

