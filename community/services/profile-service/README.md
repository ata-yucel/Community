# profile-service

Kullanıcı profilleri. İki süreç, tek imaj:

- **API** (`app/main.py`): `GET/PUT /me` — kimliği gateway'in koyduğu
  `X-User-Id` başlığından alır (token doğrulama Traefik ForwardAuth ile
  auth-service `/verify`'da yapılır; bu serviste JWT kodu yoktur).
- **Tüketici** (`app/consumer.py`, ayrı konteyner `profile-consumer`):
  RabbitMQ'daki `user.registered` olayını dinler, profili idempotent
  şekilde oluşturur (user_id PK + ON CONFLICT DO NOTHING).

Detaylar ve olay akışı: [../../README.md](../../README.md)
