# Menggunakan image Python resmi versi 3.11 slim sebagai base
FROM python:3.11-slim

# Set direktori kerja di container
WORKDIR /app

# Salin requirements.txt ke container
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file script ke dalam container
COPY . .

# Jalankan bot Python
CMD ["python", "app.py"]
