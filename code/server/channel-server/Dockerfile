#FROM python:3.9-slim-buster
FROM python:3.9-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

# CMD ["python3", "channelserver.py"]
CMD ["twistd", "--nodaemon", "-y", "./channelserver.py"]

