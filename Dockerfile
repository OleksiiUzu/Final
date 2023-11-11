FROM python:3.10.10-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app
EXPOSE 8000
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/