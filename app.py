from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Model, Bike, User
from flask import make_response
import requests

app = Flask(__name__)
# from flask import session as login_session
# import random, string
#
# from oauth2client.client import flow_from_clientsecrets
# from oauth2client.client import FlowExchangeError
# import httplib2
# import json

# CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Bike Exchange Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///bikecatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# @app.route('/model/JSON')

# Initial Database
# model = {'name': 'MTB', 'id': '1', 'user_id': '1'}
# models = [{'name': 'MTB', 'id': '1', 'user_id': '1'}, {'name':'CX', 'id':'2', 'user_id': '1'},{'name':'Road', 'id':'3', 'user_id': '1'}]
#
# bike = {'name': 'Huffy 24', 'id': '1', 'description': 'This is the best Mountain Bike ever!', 'price': '$120', 'type_id': '1', 'user_id': '1'}
#
# bikes = [{'name': 'Huffy 24', 'id': '1', 'description': 'This is the best Mountain Bike ever!', 'price': '$120', 'type_id': '1', 'user_id': '1'}, {'name': 'Trinx Free 2', 'id': '2', 'description': 'This is the best Hybrid ever!', 'price': '$200', 'type_id': '1', 'user_id': '1'}, {'name': 'Huffy 29', 'id': '3', 'description': 'This is the BIGGEST Mountain Bike ever!', 'price': '$500', 'type_id': '1', 'user_id': '1'}]

# Landing page
@app.route('/')
def landingPage():
    return render_template('index.html')


# Show all models
@app.route('/explore/')
def showModels():
    models = session.query(Model).all()
    return render_template('explore.html', models=models)


# Create a new model
@app.route('/explore/model/new/', methods=['GET', 'POST'])
def newModel():
    if request.method == 'POST':
        newModel = Model(name=request.form['name'])
        session.add(newModel)
        session.commit()
        return redirect(url_for('showModels'))
    else:
        return render_template('newModel.html')


# Edit a model
@app.route('/explore/model/<string:model_name>/edit/', methods=['GET', 'POST'])
def editModel(model_name):
    editedModel = session.query(Model).filter_by(name=model_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedModel.name = request.form['name']
            return redirect(url_for('showModels'))
    else:
        return render_template('editModel.html', model=editedModel)


# Delete a model
@app.route('/explore/model/<string:model_name>/delete/', methods=['GET', 'POST'])
def deleteModel(model_name):
    modelToDelete = session.query(Model).filter_by(name=model_name).one()
    if request.method == 'POST':
        session.delete(modelToDelete)
        session.commit()
        return redirect(url_for('showModels'))
    else:
        return render_template('deleteModel.html', model=modelToDelete)


# Show a model's listings
@app.route('/explore/model/<string:model_name>/')
def showBikes(model_name):
    model = session.query(Model).filter_by(name=model_name).one()
    try:
        session.query(Bike).filter_by(type_id=model.id).one()
        listings = session.query(Bike).filter_by(type_id=model.id).all()
        return render_template('listBikes.html', bikes=listings, model=model)
    except:
        return render_template('emptyModel.html', model=model)


# Create a new listing
@app.route('/explore/model/<string:model_name>/new/', methods=['GET', 'POST'])
def newBike(model_name):
    if request.method == 'POST':
        type = session.query(Model).filter_by(name=model_name).one()
        newBike = Bike(name=request.form['name'], description=request.form['desc'], price=request.form['price'], type_id=type.id)
        session.add(newBike)
        session.commit()
        return redirect(url_for('showBikes', model_name=model_name))
    else:
        return render_template('newBike.html')


# View a listing
@app.route('/explore/model/<string:model_name>/<string:listing_name>/', methods=['GET', 'POST'])
def thisBike(model_name, listing_name):
    model = session.query(Model).filter_by(name=model_name).one()
    bike = session.query(Bike).filter_by(name=listing_name).one()
    return render_template('viewBike.html', model=model, bike=bike)


# Edit a listing
@app.route('/explore/model/<string:model_name>/<string:listing_name>/edit', methods=['GET', 'POST'])
def editBike(model_name, listing_name):
    model = session.query(Model).filter_by(name=model_name).one()
    editedBike = session.query(Bike).filter_by(name=listing_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBike.name = request.form['name']
        if request.form['desc']:
            editedBike.description = request.form['desc']
        if request.form['price']:
            editedBike.price = request.form['price']
        session.add(editedBike)
        session.commit()
        return redirect(url_for('thisBike', model_name=model_name, listing_name=editedBike.name))
    else:
        return render_template('editBike.html', bike=editedBike, model=model)



# Delete a listing
@app.route('/explore/model/<string:model_name>/<string:listing_name>/delete', methods=['GET', 'POST'])
def deleteBike(model_name, listing_name):
    model = session.query(Model).filter_by(name=model_name).one()
    delBike = session.query(Bike).filter_by(name=listing_name).one()
    if request.method == 'POST':
        session.delete(delBike)
        session.commit()
        return redirect(url_for('showBikes', model_name=model_name))
    else:
        return render_template('deleteBike.html', bike=delBike, model=model)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
