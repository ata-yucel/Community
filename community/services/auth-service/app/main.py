from fastapi import FastAPI

# Faz 0 iskeleti: sadece servisin ayakta ve gateway arkasından
# erişilebilir olduğunu kanıtlayan iki endpoint. Gerçek auth mantığı
# (kayıt, login, JWT, user.registered event'i) bir sonraki adımda gelecek.

app = FastAPI(title="Auth Service", version="0.1.0")


@app.get("/")
async def root():
    return {"service": "auth", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
