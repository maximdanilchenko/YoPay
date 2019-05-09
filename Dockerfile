FROM python:3.7-alpine3.9 as builder

RUN apk add --no-cache \
    git \
    make \
    gcc \
    linux-headers \
    libc-dev \
    openssl-dev \
    libffi-dev \
    g++ \
    postgresql-dev

ADD requirements.txt /app/
WORKDIR /app
RUN pip3 install --upgrade -r requirements.txt

FROM builder as develop
ADD dev-requirements.txt /app/
RUN pip3 install --upgrade -r dev-requirements.txt
EXPOSE 8765

FROM builder as test
ADD dev-requirements.txt /app/
RUN pip3 install --upgrade -r dev-requirements.txt
ADD . /app
