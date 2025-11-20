# NFT Ticketing Platform - Backend Setup

## Supabase Integration Complete! ✅

### Database Schema
Aşağıdakı cədvəllər yaradılıb və hazırdır:

1. **wallets** - İstifadəçi wallet məlumatları və balansları
2. **venues** - Tədbir məkanları
3. **events** - Tədbirlər və bilet məlumatları
4. **tickets** - NFT biletlər
5. **orders** - Bilet alış-veriş sifarişləri
6. **resales** - İkinci əl bazar üçün satışlar
7. **scanners** - Bilet skan cihazları
8. **scans** - Bilet doğrulama qeydləri

### Hazır Məlumatlar
3 nümunə venue (tədbir məkanı) əlavə edilib:
- Baku Crystal Hall (25,000 tutum)
- Heydar Aliyev Palace (3,500 tutum)
- Baku Congress Center (4,000 tutum)

## Quraşdırma Addımları

### 1. Environment Variables Ayarları

`.env.new` faylını `.env` olaraq yenidən adlandırın və Supabase service role key-ni əlavə edin:

```bash
mv .env.new .env
```

Sonra `.env` faylında `SUPABASE_KEY` dəyərini dəyişdirin:

1. Supabase Dashboard-a gedin: https://supabase.com/dashboard/project/cuaztkzrtnuoviomfwrz/settings/api
2. "service_role" key-i kopyalayın (eyJhbGci... ilə başlayan uzun string)
3. `.env` faylında `your-service-role-key-here` əvəzinə yapışdırın

### 2. Virtual Environment Yaratma (əgər yoxdursa)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# və ya
venv\Scripts\activate  # Windows
```

### 3. Dependencies Quraşdırma

```bash
pip install -r requirements.txt
```

### 4. Serveri İşə Salma

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Server işə düşəcək: http://localhost:8000

### 5. API Documentation

FastAPI avtomatik dokumentasiya təmin edir:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Wallets
- `POST /api/wallet/connect` - Wallet qoşma
- `GET /api/wallet/{address}` - Wallet məlumatları

### Venues
- `POST /api/venues` - Yeni venue yaratma
- `GET /api/venues` - Bütün venue-ları əldə etmə

### Events
- `POST /api/events` - Yeni tədbir yaratma
- `GET /api/events` - Bütün tədbirləri əldə etmə
- `GET /api/events/{event_id}` - Konkret tədbir məlumatı

### Tickets
- `POST /api/tickets/mint` - Yeni bilet yaratma (mint)
- `GET /api/tickets/wallet/{wallet_address}` - Wallet-ə aid biletlər
- `GET /api/tickets/{ticket_id}` - Konkret bilet məlumatı

### Marketplace/Resale
- `POST /api/marketplace/list` - Bileti satışa çıxarma
- `GET /api/marketplace/listings` - Satışdakı biletlər
- `POST /api/marketplace/buy` - İkinci əldən bilet alma

### Scanners
- `POST /api/scanner/register` - Yeni scanner qeydiyyatı
- `POST /api/scanner/verify` - Bileti doğrulama (scan)
- `GET /api/scans/venue/{venue_id}` - Venue-ya aid skanlar

## Test Etmə

### 1. Wallet yaratma:
```bash
curl -X POST "http://localhost:8000/api/wallet/connect" \
  -H "Content-Type: application/json" \
  -d '{"address": "0x1234567890123456789012345678901234567890"}'
```

### 2. Tədbir yaratma:
```bash
curl -X POST "http://localhost:8000/api/events" \
  -H "Content-Type: application/json" \
  -d '{
    "venue_id": 1,
    "name": "Bakıda Jazz Gecəsi",
    "description": "Məşhur jazz ifaçıları ilə xüsusi gecə",
    "event_date": "2025-12-31",
    "total_supply": 500,
    "base_price": 50.0
  }'
```

### 3. Bilet alma:
```bash
curl -X POST "http://localhost:8000/api/tickets/mint" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "buyer_address": "0x1234567890123456789012345678901234567890"
  }'
```

## Database Əlaqəsi

### Supabase Dashboard
Databazı vizual olaraq idarə etmək üçün:
https://supabase.com/dashboard/project/cuaztkzrtnuoviomfwrz/editor

### Birbaşa SQL Sorğuları
Supabase SQL Editor:
https://supabase.com/dashboard/project/cuaztkzrtnuoviomfwrz/sql/new

## Troubleshooting

### Database connection error
- `.env` faylında SUPABASE_KEY düzgün olduğunu yoxlayın
- Service role key istifadə etdiyinizdən əmin olun (anon key deyil)

### Tables not found
- Migrasiya tətbiq olunduğunu yoxlayın: `create_tables.sql` faylı
- Supabase Dashboard-dan cədvəlləri yoxlayın

### CORS errors (frontend ilə işləyərkən)
- `server.py`-da CORS middleware konfiqurasiyasını yoxlayın
- Frontend URL-ini allow_origins siyahısına əlavə edin

## Proyekt Strukturu

```
backend/
├── server.py              # Ana FastAPI server
├── .env                   # Environment variables (SECRET!)
├── .env.example          # Environment template
├── .env.new              # Yeni konfiqurasiya (rename to .env)
├── requirements.txt       # Python dependencies
├── create_tables.sql     # Database schema
└── README_SETUP.md       # Bu fayl
```

## Production Deployment

Production üçün:
1. DEBUG mode-u söndürün
2. SECRET_KEY istifadə edin
3. HTTPS-dən istifadə edin
4. Rate limiting əlavə edin
5. Proper authentication/authorization tətbiq edin
6. Environment variables-i secure şəkildə saxlayın

## Next Steps

1. Frontend-i backend-ə qoşun
2. Blockchain integrasiyası əlavə edin (əgər lazımsa)
3. Payment gateway integrasiyası
4. Email notifications
5. QR code generation üçün biletlər
6. Analytics və reporting

---

**Proyekt URL:** https://cuaztkzrtnuoviomfwrz.supabase.co
**Region:** ap-northeast-1 (Tokyo)
**Database:** PostgreSQL 17.6

✅ Database hazırdır
✅ API endpoints hazırdır
✅ Test məlumatları əlavə edilib
✅ İstifadəyə hazırdır!
