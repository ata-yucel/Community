import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Button,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth-context";
import { hataMesaji } from "../../lib/errors";

type Profile = {
  user_id: string;
  display_name: string;
  bio: string | null;
  created_at: string;
  updated_at: string;
};

export default function Profil() {
  const { user, logout } = useAuth();
  const [profil, setProfil] = useState<Profile | null>(null);
  const [hata, setHata] = useState<string | null>(null);

  // Düzenleme kipi: taslaklar ayrı state'te durur; Vazgeç hiçbir şeyi bozmaz.
  const [duzenleme, setDuzenleme] = useState(false);
  const [adTaslak, setAdTaslak] = useState("");
  const [bioTaslak, setBioTaslak] = useState("");
  const [kaydediliyor, setKaydediliyor] = useState(false);
  const [kipHata, setKipHata] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const p = await apiFetch<Profile>("/profile/me", { auth: true });
        setProfil(p);
      } catch (e) {
        setHata(hataMesaji(e));
      }
    })();
  }, []);

  function duzenlemeyeGec() {
    if (!profil) return;
    setAdTaslak(profil.display_name);
    setBioTaslak(profil.bio ?? "");
    setKipHata(null);
    setDuzenleme(true);
  }

  async function kaydet() {
    setKipHata(null);
    setKaydediliyor(true);
    try {
      const guncel = await apiFetch<Profile>("/profile/me", {
        method: "PUT",
        auth: true,
        // bio boşaltıldıysa null gönderilir: backend bunu "bilinçli temizleme"
        // sayar. display_name boş gönderilmez (Kaydet düğmesi kilitli).
        body: {
          display_name: adTaslak.trim(),
          bio: bioTaslak.trim() === "" ? null : bioTaslak.trim(),
        },
      });
      setProfil(guncel);
      setDuzenleme(false);
    } catch (e) {
      setKipHata(hataMesaji(e));
    } finally {
      setKaydediliyor(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.etiket}>E-posta</Text>
      <Text style={styles.deger}>{user?.email}</Text>

      {profil === null && hata === null && <ActivityIndicator />}
      {hata && <Text style={styles.hata}>{hata}</Text>}

      {profil && !duzenleme && (
        <>
          <Text style={styles.etiket}>Görünen ad</Text>
          <Text style={styles.deger}>{profil.display_name}</Text>
          <Text style={styles.etiket}>Hakkımda</Text>
          <Text style={styles.deger}>{profil.bio ?? "(boş)"}</Text>
          <View style={styles.dugme}>
            <Button title="Düzenle" onPress={duzenlemeyeGec} />
          </View>
        </>
      )}

      {profil && duzenleme && (
        <>
          <Text style={styles.etiket}>Görünen ad</Text>
          <TextInput
            style={styles.input}
            value={adTaslak}
            onChangeText={setAdTaslak}
            maxLength={50}
          />
          <Text style={styles.etiket}>Hakkımda</Text>
          <TextInput
            style={[styles.input, styles.bioInput]}
            value={bioTaslak}
            onChangeText={setBioTaslak}
            maxLength={500}
            multiline
            placeholder="(boş bırakırsan temizlenir)"
          />
          {kipHata && <Text style={styles.hata}>{kipHata}</Text>}
          {kaydediliyor ? (
            <ActivityIndicator />
          ) : (
            <View style={styles.dugmeSatiri}>
              <View style={styles.dugmeYarim}>
                <Button title="Vazgeç" color="#888" onPress={() => setDuzenleme(false)} />
              </View>
              <View style={styles.dugmeYarim}>
                <Button title="Kaydet" onPress={kaydet} disabled={!adTaslak.trim()} />
              </View>
            </View>
          )}
        </>
      )}

      <View style={styles.cikis}>
        <Button title="Çıkış Yap" color="#c00" onPress={() => void logout()} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 6,
  },
  etiket: {
    color: "#888",
    fontSize: 13,
    marginTop: 12,
  },
  deger: {
    fontSize: 17,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 12,
    fontSize: 17,
  },
  bioInput: {
    minHeight: 80,
    textAlignVertical: "top",
  },
  hata: {
    color: "#c00",
    marginTop: 12,
  },
  dugme: {
    marginTop: 16,
  },
  dugmeSatiri: {
    flexDirection: "row",
    gap: 12,
    marginTop: 16,
  },
  dugmeYarim: {
    flex: 1,
  },
  cikis: {
    marginTop: "auto",
  },
});
