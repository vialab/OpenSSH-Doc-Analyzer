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

RUN pip install flask numpy scikit-learn==0.20 scipy==1.2.0 pypdf2 pdfminer wand matplotlib==2.2.4 \
opencv-python pandas textstat mysqlclient lxml simplejson nltk lz4 treetaggerwrapper unicodecsv pathlib2

ENV FLASK_APP file_upload.py

WORKDIR /usr/src/app

COPY . /usr/src/app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
