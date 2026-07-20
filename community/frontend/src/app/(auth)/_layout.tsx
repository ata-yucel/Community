import { Stack } from "expo-router";

// Giriş yapılmamışken görünen ekranlar. İlk sıradaki ekran (login)
// grubun açılış ekranıdır.

export default function AuthLayout() {
  return (
    <Stack>
      <Stack.Screen name="login" options={{ title: "Giriş Yap" }} />
      <Stack.Screen name="register" options={{ title: "Kayıt Ol" }} />
    </Stack>
  );
}
