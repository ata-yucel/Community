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

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [sifre, setSifre] = useState("");
  const [hata, setHata] = useState<string | null>(null);
  const [gonderiliyor, setGonderiliyor] = useState(false);

  async function girisYap() {
    setHata(null);
    setGonderiliyor(true);
    try {
      await login(email.trim(), sifre);
      // Yönlendirme gerekmez: user dolunca kök korumalar (app) grubunu
      // açar ve router profili kendisi gösterir.
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
        placeholder="Şifre"
        secureTextEntry
        value={sifre}
        onChangeText={setSifre}
      />
      {hata && <Text style={styles.hata}>{hata}</Text>}
      {gonderiliyor ? (
        <ActivityIndicator />
      ) : (
        <Button title="Giriş Yap" onPress={girisYap} disabled={!email || !sifre} />
      )}
      <Link href="/register" style={styles.link}>
        Hesabın yok mu? Kayıt ol
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
  link: {
    textAlign: "center",
    color: "#1a73e8",
    marginTop: 8,
  },
});
