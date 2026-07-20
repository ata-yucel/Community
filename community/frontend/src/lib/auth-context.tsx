import * as SecureStore from "expo-secure-store";
import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { ApiError, apiFetch, setAuthToken, setOnUnauthorized } from "./api";

// Oturumun tek sahibi. Token telefonun şifreli kasasında (SecureStore)
// durur; uygulama açılışında /auth/me ile hâlâ geçerli mi diye bakılır.
// user === null ise kök düzendeki korumalar login ekranına düşürür.

const TOKEN_KEY = "access_token";

type User = {
  id: string;
  email: string;
};

type TokenOut = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

type AuthState = {
  yukleniyor: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth yalnızca AuthProvider içinde kullanılabilir");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [yukleniyor, setYukleniyor] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  async function logout() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
  }

  useEffect(() => {
    // Korumalı bir istek 401 dönerse (örn. token süresi doldu) api.ts bu
    // kancayı çağırır: oturum temizlenir, korumalar login'e düşürür.
    setOnUnauthorized(() => {
      void logout();
    });

    // Açılış: kasada token varsa doğrula, yoksa doğrudan login'e.
    (async () => {
      try {
        const token = await SecureStore.getItemAsync(TOKEN_KEY);
        if (token) {
          setAuthToken(token);
          const me = await apiFetch<User>("/auth/me", { auth: true });
          setUser(me);
        }
      } catch {
        // Geçersiz token veya ağ hatası: temiz başlangıç, login ekranı.
        await logout();
      } finally {
        setYukleniyor(false);
      }
    })();

    return () => setOnUnauthorized(null);
  }, []);

  async function login(email: string, password: string) {
    const t = await apiFetch<TokenOut>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    await SecureStore.setItemAsync(TOKEN_KEY, t.access_token);
    setAuthToken(t.access_token);
    const me = await apiFetch<User>("/auth/me", { auth: true });
    setUser(me);
  }

  async function register(email: string, password: string) {
    await apiFetch("/auth/register", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    const t = await apiFetch<TokenOut>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    await SecureStore.setItemAsync(TOKEN_KEY, t.access_token);
    setAuthToken(t.access_token);

    // Profil, kayıt olayıyla asenkron oluşur (~1-2 sn). user'ı hemen
    // doldursak korumalar döner ve Profil ekranı 404 gösterirdi; o yüzden
    // önce profil hazır mı diye yokla, SONRA user'ı doldur.
    for (let deneme = 1; deneme <= 6; deneme++) {
      try {
        await apiFetch("/profile/me", { auth: true });
        break;
      } catch (e) {
        const gecici404 = e instanceof ApiError && e.status === 404;
        if (!gecici404) throw e;
        // 6. denemede de 404 ise yine de içeri al: Profil ekranı kendi
        // 404'ünü gösterir — bu "tüketici düşük" sinyalidir, gizlenmez.
        if (deneme < 6) await new Promise((coz) => setTimeout(coz, 1000));
      }
    }

    const me = await apiFetch<User>("/auth/me", { auth: true });
    setUser(me);
  }

  return (
    <AuthContext.Provider value={{ yukleniyor, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
