FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create photos directory
RUN mkdir -p /app/photos

CMD ["python", "-m", "bot.main"]
