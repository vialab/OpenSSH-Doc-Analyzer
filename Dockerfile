FROM ubuntu:18.04

RUN sed -i 's/archive.ubuntu.com/mirror.science.uoit.ca/g' \
        /etc/apt/sources.list

ENV TZ=America/Toronto
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /usr/src/app


RUN apt-get update && apt-get install -y \
        build-essential \
        python3.7-dev \
        python3-pip \
        python3-tk \
        libmagickwand-dev \
        libmysqlclient-dev \
    && python3.7 -m pip install --upgrade pip 

RUN python3.7 -m pip install -U setuptools

COPY ./requirements.txt /usr/src/app/requirements.txt
# RUN pip install Werkzeug==0.14.1 flask==1.0.4 numpy==1.13.1 scikit-learn==0.20 scipy==1.2.0 pypdf2==1.26.0 pdfminer wand matplotlib==2.2.4 \
# opencv-python pandas==0.24.2 textstat mysqlclient lxml==4.0.0 simplejson nltk==3.2.4 lz4 treetaggerwrapper unicodecsv pathlib2 python-docx==0.8.10
RUN python3.7 -m pip install -r requirements.txt

RUN rm -rf /usr/share/man \
    && apt-get remove -y \
        build-essential \
        gcc-7 \ 
        libmagickwand-dev \
        libmysqlclient-dev \
    && rm -rf /root/.cache
    
RUN apt-get install -y libmysqlclient20 \
    && apt-get autoremove -y --purge && apt-get autoclean -y && apt-get purge \
    && rm -rf /var/lib/apt/lists/* 

COPY . /usr/src/app


ENV FLASK_APP file_upload.py
ENV DEPLOY_ENV PROD
ENV FLASK_ENV production
ENV FLASK_DEBUG False


WORKDIR /usr/src/app/treetagger
RUN chmod +x install-tagger.sh
RUN ./install-tagger.sh
WORKDIR /usr/src/app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
