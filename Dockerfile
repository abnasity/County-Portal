FROM python:3.11-alpine

WORKDIR /app

# Install required dependencies
RUN apk update && apk add --no-cache libpq-dev gcc && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]