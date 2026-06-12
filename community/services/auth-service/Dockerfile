FROM python:3.12-slim

WORKDIR /app

# Bağımlılıkları önce kopyala -> Docker layer cache'i daha verimli kullanılır
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# --reload sadece geliştirme içindir; prod'da kaldırılır
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
