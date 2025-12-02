# How to Start the Backend Server

## ✅ Dependencies Installed

All Python packages have been successfully installed!

## 🚀 Start the Server

**In your terminal, run:**

```bash
cd backend
source venv/bin/activate
python main.py
```

**Or use the startup script:**

```bash
cd backend
./start_backend.sh
```

## 📋 Before Starting - Verify .env File

Make sure your `.env` file has:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET_KEY=iQuXLoySsSqoC9J8Mq_5lQKPsXcwqs-mZlhJV4iWRlk
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## ✅ Verify Server is Running

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test it:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

## 🌐 Access Points

- **API Base URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Troubleshooting

### Server won't start
1. Check `.env` file has all required variables
2. Make sure virtual environment is activated: `source venv/bin/activate`
3. Check for errors in terminal output

### Port 8000 already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in main.py (line 63)
```

### Import errors
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 Next Steps

1. ✅ Start backend server (this file)
2. ✅ Start frontend: `cd frontend && npm run dev`
3. ✅ Test registration at http://localhost:5173/register

