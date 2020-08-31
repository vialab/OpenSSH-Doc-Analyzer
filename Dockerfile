FROM python:3.7-slim as builder

# ENV TZ=America/Toronto
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /usr/src/app

RUN apt update \
    && apt upgrade -y

RUN apt install -y \
    build-essential \ 
    python3.7-dev \
    libmariadb-dev-compat \
    libssl-dev \
    liblz4-dev \
    pkg-config \
    acl-dev \
    linux-headers-amd64 \
    libfuse-dev \
    attr-dev

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN python3.7 -m pip install --upgrade pip \
    && python3.7 -m pip install -r requirements.txt

FROM python:3.7-slim

COPY . /usr/src/app
RUN apt update \
    && apt upgrade -y \
    && apt install -y \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages

ENV FLASK_APP file_upload.py
ENV DEPLOY_ENV PROD
ENV FLASK_ENV production
ENV FLASK_DEBUG False

WORKDIR /usr/src/app/treetagger
RUN chmod +x install-tagger.sh
RUN ./install-tagger.sh
WORKDIR /usr/src/app

EXPOSE 5000

CMD ["python3.7", "-m", "flask", "run", "--host=0.0.0.0"]