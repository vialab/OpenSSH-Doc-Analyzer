# Synonymic Search / Journal Matching

The synonymic search project is aimed at humanities researchers trying to ask more intelligent questions of document corpora. Our stakeholders identified to us that as document collections get larger, there is an inverse relationship to their ability to find what they are looking for. In the past this has been addressed with novel methods of query generation, but we wanted to offer a different method for building intelligent queries. The synonymic search uses a navigable visual thesaurus to allow for query extensions. Users can upload documents, which me model and then direct to similar matches, but can also input keywords and then navigate a hierarchy of English and French synonyms that are categorically related. The overall goal of this project was to allow for dynamic query generation especially when the user is not completely certain of what they are searching for. We imagine that through this interface humanities researchers can augment their search process to find more relevant results in large document corpora.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This software was created in PYTHON 2.7 and is not compatible with more up to date versions.

A database connection is required for proper functioning of this software. You may connect to your local database by providing your own `dbconfig.py` file in the `./static/py/` directory. Alternatively, you may pass the `DATABASE_URL` environment variable a database string to the FLASK instance. An example is provided:

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

Install and activate a Python 2.7 virtual environment (virtualenv):

```
cd /path/to/OpenSSH-Doc-Analyzer
virtualenv venv
source venv/bin/activate
```
Install Python dependencies:

```
pip install Werkzeug==0.14.1 flask numpy scikit-learn==0.20 scipy==1.2.0 pypdf2 pdfminer wand matplotlib==2.2.4 \
opencv-python pandas textstat mysqlclient lxml simplejson nltk lz4 treetaggerwrapper unicodecsv pathlib2
```
Note: `pip install -r requirements.txt` might work as well (not tested)

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

### Debugging

All development was done using [Visual Studio Code] (https://code.visualstudio.com/), and thus the `/.vscode` files have been provided in order for easy debugging of code. Simply, install the IDE, along with the Python package (in the IDE), select your debug options to Flask (note this is not the same as Flask (Old)) and press play.

The project should be available at the URL:
```
http://localhost:5000/
```

## Deployment

Pushes to this repository are picked up by DockerHub, which automatically rebuilds the docker image. Using Kubernetes, deployment to production is automated, and thus, please be cautious when pushing your code to the master branch. Database connections, and volume mounting is managed in the automation process.


## Built With

* [Flask](http://flask.pocoo.org/) - The web framework used (PYTHON 2.7)
* [Jinja2](http://jinja.pocoo.org/docs/2.10/) - Template engine
* [Bootstrap](https://getbootstrap.com/) - Front-end component library
* [D3](https://d3js.org/) - JS visualization library
* [MySQL](https://www.mysql.com/) - Database back-end
* [Docker](https://www.docker.com/) - Container / Dependency management

## Versioning

This project is being developed using an iterative approach. Therefore, now releases have yet been made and the project will be subject to drastic changes. No versioning practices will be followed until release. To see a history of changes made to this project, see [commit history](https://github.com/vialab/OpenSSH-Doc-Analyzer/commits/).

## Authors

* Adam Bradley, PhD. - Research Associate
* Christopher Collins, PhD. - Research Supervisor
* Victor (Jay) Sawal, BSc. - Software Developer

## License

This research was conducted as part of the CO.SHS project (co-shs.ca) and has received financial support from the Canada Foundation for Innovation (Cyberinfrastructure Initiative – Challenge 1 – First competition).

## Acknowledgments

* Richard Drake, MSc. - Laboratory Technician (Science Building)
