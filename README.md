# Wolfgang Bike Catalog v1.0 -- [app.py](app.py) -- 01/10/2018

This is a simple web application created in fulfillment of Udacity's Full Stack Web Developer NanoDegree.
The aim of this project is to create a OAuth secured, fully CRUD operational item catalog using Flask and Python.

## Dependencies
- Python 2.7.12 or higher (Download [here](https://www.python.org/downloads/))
- VirtualBox  5.1.38 r122592 (Qt5.6.2) (Download [here](https://www.virtualbox.org/wiki/Downloads))
- Vagrant 2.1.2 (Download [here](https://www.vagrantup.com/downloads.html))
- Flask 1.0.2 or higher (Download [here](http://flask.pocoo.org/))
- SQLAlchemy 1.2.12 or higher (Download [here](https://docs.sqlalchemy.org/en/latest/intro.html))

## Contents
The database contains 3 tables: **Users, Models, & Bikes**
These tables hold information about the users, the bike models on offer, and the individual bike listings - all associated to their original creator.

## Setup/Installation
- Once you have vagrant setup on VirtualBox you can use your terminal to start the VM using `vagrant up` _(Note: this will take a while the first time you launch as vagrant is downloading extra dependencies)_
- Follow that with `vagrant ssh` to log into your VM _(Note: On some Windows systems, you will need to use `winpty vagrant ssh` instead of `vagrant ssh`)_
- Navigate to the repo's directory and run `pip  install  -r requirements.txt`
- Run the web-app using the command `python app.py`

## Usage
This program can easily run from the command line using: `python app.py`
If you're using python 3 you may need to use `python3 app.py`

## License
 The content of this repository is created by Bishoy Maher and is licensed under the [MIT License](LICENSE.md)
