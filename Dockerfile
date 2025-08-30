# Gunakan image python slim versi 3.11
FROM python:3.11-slim

# Set working directory di container
WORKDIR /app

# Salin semua file ke container
COPY . .

# Install dependencies dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan script python utama
CMD ["python", "app.py"]
