FROM python:3.11-slim

# FFmpeg ස්ථාපනය (yt-dlp merge සඳහා අවශ්‍ය)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway එකේ PORT එක dynamic ව ලබාගන්න මෙසේ වෙනස් කරන්න
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
