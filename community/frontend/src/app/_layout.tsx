import { Stack } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { AuthProvider, useAuth } from "../lib/auth-context";

// Kök düzen. "Giriş yoksa login'e at" kuralının yaşadığı TEK yer:
// user durumuna göre (auth) veya (app) grubu erişilebilir olur;
// erişilemeyen gruba gitmeye çalışan router otomatik yönlendirilir.

function RootNavigator() {
  const { yukleniyor, user } = useAuth();

  if (yukleniyor) {
    // Kasadaki token /auth/me ile doğrulanırken kısa bekleme ekranı.
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={user === null}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
      <Stack.Protected guard={user !== null}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  );
}
