FROM python:3.8-slim-buster

WORKDIR /app
COPY requirements.txt requirements.txt

RUN pip3 --version
RUN python3 --version

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "application-base.py"]