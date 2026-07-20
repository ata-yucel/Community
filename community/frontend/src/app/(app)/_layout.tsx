import { Stack } from "expo-router";

// Yalnızca giriş yapılmışken erişilebilen ekranlar.

export default function AppLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Profil" }} />
    </Stack>
  );
}
