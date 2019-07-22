FROM ubuntu:16.04

RUN sed -i 's/archive.ubuntu.com/mirror.science.uoit.ca/g' \
        /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
        build-essential \
        python-dev \
        python-pip \
        python-tk \
        libmagickwand-dev \
        libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U setuptools

RUN pip install Werkzeug==0.14.1 flask==1.0.4 numpy==1.13.1 scikit-learn==0.20 scipy==1.2.0 pypdf2==1.26.0 pdfminer wand matplotlib==2.2.4 \
opencv-python pandas==0.24.2 textstat mysqlclient lxml==4.0.0 simplejson nltk==3.2.4 lz4 treetaggerwrapper unicodecsv pathlib2 python-docx==0.8.10

ENV FLASK_APP file_upload.py
ENV DEPLOY_ENV PROD

WORKDIR /usr/src/app

COPY . /usr/src/app

WORKDIR /usr/src/app/treetagger
RUN chmod +x install-tagger.sh
RUN ./install-tagger.sh
WORKDIR /usr/src/app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
