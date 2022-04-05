FROM python:3.9-slim-buster

ENV DSW_CONFIG /app/config.yml
ENV MAILER_WORKDIR /app/templates
ENV MAILER_MODE wizard

WORKDIR /app

RUN mkdir -p /tmp/mailer

RUN apt-get update && apt-get install -qq -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app
RUN python setup.py install

CMD ["dsw-mailer", "run"]
