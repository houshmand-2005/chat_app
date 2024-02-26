FROM python:3.12.2-slim
COPY . /app/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y curl
