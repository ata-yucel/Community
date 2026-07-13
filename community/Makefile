# $RANDOM gibi bash özellikleri için (Linux'ta /bin/sh = dash olabilir)
SHELL := /bin/bash

.PHONY: up down clean logs ps restart auth-logs profile-logs consumer-logs queues smoke

up:            ## Tüm servisleri ayağa kaldır (build dahil)
	docker compose up -d --build

down:          ## Servisleri durdur (volume'lar kalır)
	docker compose down

clean:         ## Servisleri durdur ve volume'ları sil (TÜM VERİ GİDER)
	docker compose down -v

logs:          ## Tüm logları takip et
	docker compose logs -f

auth-logs:     ## Sadece auth servisinin logları
	docker compose logs -f auth-service

profile-logs:  ## Sadece profil servisinin logları
	docker compose logs -f profile-service

consumer-logs: ## Sadece olay tüketicisinin logları
	docker compose logs -f profile-consumer

queues:        ## RabbitMQ kuyruk durumu (mesaj sayıları, tüketiciler)
	docker compose exec rabbitmq rabbitmqctl list_queues name messages messages_unacknowledged consumers

ps:            ## Çalışan servisleri listele
	docker compose ps

restart:       ## Yeniden başlat
	docker compose down && docker compose up -d --build

smoke:         ## Uçtan uca duman testi: register -> login -> me -> profil -> güncelle
	@set -e; \
	EMAIL="smoke-$$RANDOM@test.com"; \
	echo "1/5 register ($$EMAIL)"; \
	curl -sf http://localhost/api/auth/register -H 'Content-Type: application/json' \
	  -d "{\"email\":\"$$EMAIL\",\"password\":\"smokepass123\"}" > /dev/null; \
	echo "2/5 login"; \
	TOKEN=$$(curl -sf http://localhost/api/auth/login -H 'Content-Type: application/json' \
	  -d "{\"email\":\"$$EMAIL\",\"password\":\"smokepass123\"}" \
	  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'); \
	echo "3/5 auth me"; \
	curl -sf http://localhost/api/auth/me -H "Authorization: Bearer $$TOKEN" > /dev/null; \
	echo "4/5 profil (olayin islenmesi bekleniyor...)"; \
	ok=0; for i in 1 2 3 4 5 6 7 8 9 10; do \
	  if curl -sf http://localhost/api/profile/me -H "Authorization: Bearer $$TOKEN" > /dev/null; then ok=1; break; fi; \
	  sleep 1; \
	done; \
	if [ $$ok -ne 1 ]; then echo "SMOKE FAIL: profil olusmadi (profile-consumer calisiyor mu? make consumer-logs)"; exit 1; fi; \
	echo "5/5 profil guncelle"; \
	curl -sf -X PUT http://localhost/api/profile/me -H "Authorization: Bearer $$TOKEN" \
	  -H 'Content-Type: application/json' -d '{"bio":"smoke testi"}' > /dev/null; \
	echo "SMOKE OK"
