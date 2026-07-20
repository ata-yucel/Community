import { ApiError } from "./api";

// Kullanıcıya gösterilecek Türkçe hata metinleri. Teknik detay
// (durum kodu, stack) ekrana sızmaz.

export function hataMesaji(e: unknown): string {
  if (e instanceof ApiError) {
    switch (e.status) {
      case 401:
        return "E-posta veya şifre hatalı.";
      case 404:
        return "Kayıt bulunamadı.";
      case 409:
        return "Bu e-posta zaten kayıtlı.";
      case 422:
        return "Geçersiz bilgi: e-posta biçimini ve şifrenin en az 8 karakter olduğunu kontrol et.";
      default:
        return "Bir şeyler ters gitti. Lütfen tekrar dene.";
    }
  }
  if (e instanceof TypeError) {
    // fetch, sunucuya hiç ulaşamazsa TypeError fırlatır.
    return "Sunucuya ulaşılamadı. Wi-Fi bağlantını ve backend'in açık olduğunu kontrol et.";
  }
  if (e instanceof Error && e.message.includes("EXPO_PUBLIC_API_URL")) {
    return e.message;
  }
  return "Beklenmedik bir hata oluştu.";
}
