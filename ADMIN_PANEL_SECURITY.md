# Admin Panel Security Configuration

This document describes the secure, separated admin panel setup for the NFT Ticketing Platform.

## Overview

The admin panel has been separated from the main application for enhanced security:

- **Main Application**: `http://localhost:5173` (public routes)
- **Admin Panel**: `http://localhost:4201/secure-admin/login` (hidden, non-guessable path)

## Architecture

### Frontend Separation

- **Main App**: `frontend/App.tsx` - Public user-facing application
- **Admin App**: `frontend/AdminApp.tsx` - Separate admin-only application
- **Admin Config**: `frontend/vite.config.admin.ts` - Separate Vite configuration for port 4201
- **Admin Entry**: `frontend/index.admin.tsx` - Admin application entry point

### Security Features

1. **Non-guessable Path**: `/secure-admin/*` instead of `/admin/*`
2. **Separate Port**: Runs on port 4201, isolated from main app
3. **No Public Links**: Admin routes removed from main application
4. **Separate Build**: Admin panel builds to `dist-admin/` directory
5. **No Indexing**: Admin HTML includes `noindex, nofollow` meta tags

## Environment Variables

### Frontend (.env)

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api

# Admin Panel Port (optional, defaults to 4201)
ADMIN_PORT=4201

# Admin Panel Path (optional, defaults to /secure-admin)
ADMIN_PATH=/secure-admin
```

### Backend (.env)

```env
# CORS Origins (include admin port)
CORS_ORIGINS=http://localhost:5173,http://localhost:4201

# Admin Credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD_HASH=your_hashed_password

# JWT Configuration
JWT_SECRET_KEY=your_secret_key_here
ADMIN_TOKEN_EXPIRE_MINUTES=480

# Environment
ENVIRONMENT=development  # or 'production'
```

## Running the Applications

### Development

1. **Start Backend** (port 8000):
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Start Main Frontend** (port 5173):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Start Admin Panel** (port 4201):
   ```bash
   cd frontend
   npm run dev:admin
   ```

### Production Build

1. **Build Main App**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Build Admin Panel**:
   ```bash
   cd frontend
   npm run build:admin
   ```

## Access URLs

- **Main Application**: `http://localhost:5173`
- **Admin Login**: `http://localhost:4201/secure-admin/login`
- **Admin Dashboard**: `http://localhost:4201/secure-admin/dashboard`

## Reverse Proxy Configuration

### Nginx Configuration

For production deployment, configure Nginx to serve both applications:

```nginx
# Main Application
server {
    listen 80;
    server_name yourdomain.com;
    
    root /path/to/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Admin Panel (Hidden, Non-guessable Path)
server {
    listen 80;
    server_name yourdomain.com;
    
    # Only allow access to /secure-admin path
    location /secure-admin {
        alias /path/to/frontend/dist-admin;
        index index.admin.html;
        
        try_files $uri $uri/ /index.admin.html;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer" always;
        
        # Rate limiting (optional)
        limit_req zone=admin_limit burst=5 nodelay;
    }
    
    # Block access to admin paths on main domain
    location ~ ^/(admin|secure-admin) {
        return 404;
    }
}
```

### Alternative: Separate Subdomain

For even better security, use a separate subdomain:

```nginx
# Admin Panel on Separate Subdomain
server {
    listen 80;
    server_name admin.yourdomain.com;
    
    root /path/to/frontend/dist-admin;
    index index.admin.html;
    
    location / {
        try_files $uri $uri/ /index.admin.html;
    }
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer" always;
    
    # IP Whitelist (optional, for extra security)
    # allow 192.168.1.0/24;
    # allow 10.0.0.0/8;
    # deny all;
}
```

## Security Best Practices

### 1. Change Default Path

The default path is `/secure-admin`, but you can change it to something even less guessable:

```typescript
// In AdminApp.tsx, change all instances of '/secure-admin' to your custom path
// Example: '/x7k9m2p4q1w8r3t6y5u0i9o7p6l5k4j3h2g1f0e9d8c7b6a5'
```

### 2. IP Whitelisting

Add IP whitelisting in your reverse proxy or firewall:

```nginx
# Nginx IP Whitelist
location /secure-admin {
    allow 192.168.1.100;  # Your office IP
    allow 10.0.0.0/8;     # VPN network
    deny all;
}
```

### 3. Rate Limiting

Implement rate limiting for admin endpoints:

```nginx
# Nginx Rate Limiting
http {
    limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=10r/m;
    
    server {
        location /secure-admin {
            limit_req zone=admin_limit burst=5 nodelay;
        }
    }
}
```

### 4. Two-Factor Authentication

Consider adding 2FA to the admin login flow for additional security.

### 5. Audit Logging

All admin actions are logged in the `admin_actions` table. Monitor these logs regularly.

### 6. Regular Security Updates

- Keep dependencies updated
- Monitor security alerts
- Review access logs regularly
- Rotate credentials periodically

## Troubleshooting

### Admin Panel Not Loading

1. Check that the admin dev server is running on port 4201
2. Verify CORS configuration includes `http://localhost:4201`
3. Check browser console for errors
4. Verify API proxy configuration in `vite.config.admin.ts`

### Authentication Issues

1. Verify backend is running on port 8000
2. Check cookie settings (SameSite, Secure flags)
3. Verify CORS credentials are enabled
4. Check browser console for cookie-related errors

### Build Issues

1. Ensure all dependencies are installed: `npm install`
2. Check that `index.admin.html` exists
3. Verify Vite config paths are correct
4. Check build output for errors

## Migration Notes

### Removing Old Admin Routes

The old admin routes (`/admin/login`, `/admin/dashboard`) have been removed from the main application. If you have bookmarks or links to these routes, update them to:

- Old: `http://localhost:5173/#/admin/login`
- New: `http://localhost:4201/secure-admin/login`

### Updating Scripts

If you have any automation scripts that access the admin panel, update them to use the new URL and port.

## Additional Security Recommendations

1. **Use HTTPS in Production**: Always use HTTPS for admin panel access
2. **VPN Access**: Restrict admin panel access to VPN-only
3. **Session Timeout**: Admin sessions expire after 8 hours (configurable)
4. **Strong Passwords**: Use strong, unique passwords for admin accounts
5. **Regular Backups**: Backup admin configuration and logs regularly
6. **Monitor Access**: Set up alerts for failed login attempts
7. **Separate Admin Network**: Consider running admin panel on a separate network segment

## Support

For issues or questions about the admin panel security setup, refer to:
- Backend API documentation: `/docs` endpoint
- Security middleware: `backend/security_middleware.py`
- Admin authentication: `backend/routers/admin_auth.py`

