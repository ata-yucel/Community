FROM python:3.12-slim

# Loglar buffer'lanmadan anında aksın; .pyc dosyası yazılmasın
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Bağımlılıkları önce kopyala -> Docker layer cache'i daha verimli kullanılır
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Konteyner root olarak çalışmasın
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# --proxy-headers: Traefik arkasında gerçek istemci IP'sini görebilmek için
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
