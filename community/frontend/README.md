# Community Mobil Uygulama

React Native + Expo (SDK 54) + TypeScript + expo-router.
Ekranlar: Giriş, Kayıt, Profil (görüntüle/düzenle, çıkış) — hepsi
`community/` backend'ine bağlanır.

## Çalıştırma

1. Backend'i başlat: `cd .. && make up && make smoke` (`SMOKE OK` görmelisin)
2. `cp .env.example .env` → içindeki IP'yi Mac'in yerel ağ IP'siyle değiştir
   (bulmak için: `ipconfig getifaddr en0`)
3. `npm install`
4. `npx expo start`
5. Telefondaki **Expo Go** uygulamasıyla QR kodu okut
   (telefon ve Mac **aynı Wi-Fi ağında** olmalı).

## Notlar

- `.env` değişince sunucuyu `npx expo start -c` ile yeniden başlat: değerler
  derleme anında gömülür, çalışırken okunmaz.
- HTTP (şifresiz) bağlantı yalnızca yerel geliştirme içindir; Expo Go bunu
  ayarsız kabul eder. Gerçek build'e (EAS) geçilirse HTTPS gerekir.
- Proje bilerek SDK 54'te: App Store'daki Expo Go istemcisi 54'te bekliyor
  ve tek test yolumuz Expo Go. Mağaza istemcisi güncellenir de proje
  açılmaz olursa: `npx expo install expo@latest --fix` ile yükselt.
- Ekran dosyaları `src/app/` altındadır (dosya = route); ekran olmayan kod
  `src/lib/` altında durur.
