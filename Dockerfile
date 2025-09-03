FROM python:3.12-slim

WORKDIR /app

# Copy dulu requirements.txt, lalu install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode source bot
COPY . .

# Jalankan bot.py (ganti sesuai nama file script Anda)
CMD ["python", "app.py"]
