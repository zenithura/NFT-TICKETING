# Setup Instructions - Environment Variables

## ⚠️ Important: Environment Files

The `.env` files are **NOT** included in the repository for security reasons. You need to create them manually.

## Backend Setup

1. **Copy the example file**:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit `.env` and fill in your values**:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Required values**:
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase anon key
   - `SUPABASE_SERVICE_KEY` - Your Supabase service role key
   - `JWT_SECRET` - Generate a random 32+ character string
   - `ADMIN_JWT_SECRET` - Generate another random 32+ character string (different from JWT_SECRET)

4. **Generate JWT secrets**:
   ```bash
   # Generate random secrets
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Frontend Setup

1. **Copy the example file**:
   ```bash
   cd frontend
   cp .env.example .env
   ```

2. **Edit `.env` and fill in your values**:
   ```bash
   nano .env
   ```

3. **Required values**:
   - `VITE_API_URL` - Backend API URL (http://localhost:8000 for development)
   - `VITE_SUPABASE_URL` - Your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` - Your Supabase anon key
   - `GEMINI_API_KEY` - Your Google Gemini API key (for chatbot)

## GitHub Actions Setup

For CI/CD to work, add these secrets in GitHub:

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each of these:

```
SUPABASE_URL          → Your Supabase project URL
SUPABASE_KEY          → Your Supabase anon key
SUPABASE_SERVICE_KEY  → Your Supabase service role key
JWT_SECRET            → Your JWT signing secret
GITGUARDIAN_API_KEY   → Your GitGuardian API key (optional)
```

## Verification

### Check Backend
```bash
cd backend
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ SUPABASE_URL:', os.getenv('SUPABASE_URL')[:20] + '...')"
```

### Check Frontend
```bash
cd frontend
cat .env | grep VITE_API_URL
```

## Security Checklist

- [ ] `.env` files created from `.env.example`
- [ ] All placeholder values replaced with real values
- [ ] `.env` files are in `.gitignore`
- [ ] GitHub Actions secrets configured
- [ ] JWT secrets are random and 32+ characters
- [ ] No secrets committed to git
- [ ] GitGuardian scan passes

## Need Help?

See `CICD_GITGUARDIAN_FIX.md` for detailed instructions.

