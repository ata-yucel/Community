.PHONY: up down logs ps restart auth-logs smoke

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

ps:            ## Çalışan servisleri listele
	docker compose ps

restart:       ## Yeniden başlat
	docker compose down && docker compose up -d --build

smoke:         ## Uçtan uca duman testi: register -> login -> me
	@set -e; \
	EMAIL="smoke-$$RANDOM@test.com"; \
	echo "1/3 register ($$EMAIL)"; \
	curl -sf http://localhost/api/auth/register -H 'Content-Type: application/json' \
	  -d "{\"email\":\"$$EMAIL\",\"password\":\"smokepass123\"}" > /dev/null; \
	echo "2/3 login"; \
	TOKEN=$$(curl -sf http://localhost/api/auth/login -H 'Content-Type: application/json' \
	  -d "{\"email\":\"$$EMAIL\",\"password\":\"smokepass123\"}" \
	  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'); \
	echo "3/3 me"; \
	curl -sf http://localhost/api/auth/me -H "Authorization: Bearer $$TOKEN" > /dev/null; \
	echo "SMOKE OK"
