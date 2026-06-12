# community — Faz 0 (platform iskeleti)

> **Not:** Asıl proje `community/` dizinindedir — compose dosyası, `.env` ve
> tüm komutlar orada çalışır. Bu dosya yalnızca genel bakış içindir.

Konum tabanlı sosyal mobil uygulamanın microservice altyapısı. Bu faz
**çalışan iskelettir**: henüz iş mantığı yok, ama gateway + veri katmanı +
message broker + tracing ayakta ve gateway arkasında referans bir Auth
servisi cevap veriyor.

## Mimari (kısa)

İstemci (Expo) → Traefik (gateway) → servisler. Her servis kendi
veritabanına sahip (database-per-service). Servisler birbirini doğrudan
çağırmak yerine RabbitMQ üzerinden event yayınlar. Her istek Jaeger ile
uçtan uca trace edilir.

## Dizin yapısı

```
community/
├── docker-compose.yml          # tüm platform tek dosyada
├── .env.example                # -> kopyala: cp .env.example .env
├── Makefile                    # make up / down / logs ...
├── infra/
│   └── postgres/
│       └── init-multiple-dbs.sh  # servis başına ayrı DB oluşturur
├── services/
│   ├── auth-service/           # ✅ referans servis (FastAPI)
│   ├── profile-service/        # ⏳ sonra (auth şablonundan klon)
│   ├── social-service/         # ⏳
│   ├── location-service/       # ⏳
│   ├── chat-service/           # ⏳
│   └── media-service/          # ⏳
└── frontend/                   # ⏳ React Native + Expo (Faz 1)
```

## Çalıştırma

Önkoşul: Docker + Docker Compose.

```bash
cp .env.example .env       # değerleri düzenle (özellikle şifreler)
make up                    # veya: docker compose up -d --build
make ps                    # her şey "running" / "healthy" mi?
```

## Doğrulama (her biri tarayıcıdan/curl ile)

| Ne | Adres | Beklenen |
|----|-------|----------|
| Gateway üzerinden Auth | http://localhost/api/auth/health | `{"status":"healthy"}` |
| Auth kök | http://localhost/api/auth/ | `{"service":"auth","status":"ok"}` |
| Traefik dashboard | http://localhost:8080 | router'lar listelenir |
| RabbitMQ yönetim UI | http://localhost:15672 | .env'deki kullanıcı/şifre |
| MinIO konsol | http://localhost:9001 | .env'deki kullanıcı/şifre |
| Jaeger UI | http://localhost:16686 | trace arayüzü |

En kritik test: `curl http://localhost/api/auth/health` → bu cevap
gelirse istemci→gateway→servis yolu çalışıyor demektir.

## Bu fazda KASITLI olarak henüz yok

- Auth'un gerçek mantığı (kayıt, login, JWT üretimi, parola hash'leme)
- `user.registered` event'inin RabbitMQ'ya basılması
- OpenTelemetry tracing kablolaması (Jaeger ayakta ama servis henüz trace yollamıyor)
- Prometheus + Grafana + Loki (metrik/log paneli)
- Diğer servisler ve frontend

Bunların hepsi sıradaki adımlarda tek tek eklenecek.

## Sıradaki adım

Auth servisini gerçek hale getirmek: Postgres'e bağlanma (SQLAlchemy +
asyncpg), kullanıcı modeli ve migration (Alembic), kayıt/login endpoint'leri,
JWT üretimi, ve `user.registered` event'i. Sonra bu servis diğerleri için
şablon olur.