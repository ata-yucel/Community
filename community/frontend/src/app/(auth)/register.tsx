import { Link } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Button,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useAuth } from "../../lib/auth-context";
import { hataMesaji } from "../../lib/errors";

export default function Register() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [sifre, setSifre] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const [gonderiliyor, setGonderiliyor] = useState(false);

  async function kayitOl() {
    setHata(null);
    setGonderiliyor(true);
    try {
      await register(email.trim(), sifre);
      // Yönlendirme gerekmez: user dolunca kök korumalar Profil'i açar.
    } catch (e) {
      setHata(hataMesaji(e));
      setGonderiliyor(false);
    }
  }

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="E-posta"
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Şifre (en az 8 karakter)"
        secureTextEntry
        value={sifre}
        onChangeText={setSifre}
      />
      {hata && <Text style={styles.hata}>{hata}</Text>}
      {gonderiliyor ? (
        <View style={styles.bekleme}>
          <ActivityIndicator />
          <Text style={styles.not}>Hesap hazırlanıyor…</Text>
        </View>
      ) : (
        <Button title="Kayıt Ol" onPress={kayitOl} disabled={!email || !sifre} />
      )}
      <Link href="/login" style={styles.link}>
        Zaten hesabın var mı? Giriş yap
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    padding: 24,
    gap: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 12,
  },
  hata: {
    color: "#c00",
    textAlign: "center",
  },
  bekleme: {
    alignItems: "center",
    gap: 8,
  },
  not: {
    textAlign: "center",
    color: "#888",
  },
  link: {
    textAlign: "center",
    color: "#1a73e8",
    marginTop: 8,
  },
});
