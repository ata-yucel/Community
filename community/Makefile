.PHONY: up down logs ps restart auth-logs

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
