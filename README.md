Repo README

# Synonymic Search / Journal Matching

The synonymic search project is aimed at humanities researchers trying to ask more intelligent questions of document corpora. Our stakeholders identified to us that as document collections get larger, there is an inverse relationship to their ability to find what they are looking for. In the past this has been addressed with novel methods of query generation, but we wanted to offer a different method for building intelligent queries. The synonymic search uses a navigable visual thesaurus to allow for query extensions. Users can upload documents, which we model and then direct to similar matches, but can also input keywords and then navigate a hierarchy of English and French synonyms that are categorically related. The overall goal of this project was to allow for dynamic query generation especially when the user is not completely certain of what they are searching for. We imagine that through this interface humanities researchers can augment their search process to find more relevant results in large document corpora.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This software was created in PYTHON 3.7 and is not compatible with more up to date versions.

A database connection is required for proper functioning of this software. You may connect to your local database by providing your own `dbconfig.py` file in the `./static/py/` directory. In order for `dbconfig.py` to be read uncomment line 1 of `db.py` which is also in `./static/py`. Alternatively, you may pass the `DATABASE_URL` environment variable a database string to the FLASK instance. An example is provided:

```
mysql = {
    "host":"localhost",
    "port":2251,
    "user":"root",
    "passwd":"123456789",
    "db":"mydatabasename"
}
```

Along with this, you will also need to install some packages (UNIX):

```
apt-get update && apt-get install -y \
        build-essential \
        python-dev \
        python-pip \
        python-tk \
        libmagickwand-dev \
        libmysqlclient-dev
```

### Installing

In order to run a local (non-containerized) version running on your machine, please run the provided commands (UNIX). 

Install and activate a Python 3.7 virtual environment (virtualenv):

```
cd /path/to/OpenSSH-Doc-Analyzer
virtualenv venv
source venv/bin/activate
```
Install Python dependencies:

```
pip install -r requirements.txt
```

Install tree tagger then go back to root folder.

```
cd treetagger
./install-tagger.sh
cd ..
```

### Get model

Make a copy of the `/model` folder that's deployed on the server that contains `synset.pkl` and `tm.gzip` (don't unzip it). Place `/model` in the project's root folder.

### Running Flask

After successfully installing you should be able to run the Flask server with the following script:

```
#!/bin/bash
echo "Starting python server.."
source venv/bin/activate
export FLASK_APP=file_upload.py
export DEPLOY_ENV=PROD #PROD
export DATABASE_URL="mysql://sshcyber:<password>@mysql.science.uoit.ca:3306/sshcyber" #PROD
flask run
echo "Python listening on http://localhost:5000"
```

## Deployment

https://synonym.vialab.ca/

Pushes to this repository are picked up by DockerHub, which automatically rebuilds the docker image. Using Kubernetes, deployment to production is automated, and thus, please be cautious when pushing your code to the master branch. Database connections, and volume mounting is managed in the automation process.


## Authors

* Adam Bradley, PhD. - Research Associate
* Christopher Collins, PhD. - Research Supervisor
* Victor (Jay) Sawal, BSc. - Software Developer

## License

This research was conducted as part of the CO.SHS project (co-shs.ca) and has received financial support from the Canada Foundation for Innovation (Cyberinfrastructure Initiative – Challenge 1 – First competition).

## Acknowledgments

* Richard Drake, MSc. - Laboratory Technician (Science Building)