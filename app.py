import requests
import random
import string
import httplib2
import json
from flask import (
                                    Flask,
                                    render_template,
                                    request,
                                    redirect,
                                    jsonify,
                                    url_for,
                                    flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Model, Bike, User
from flask import make_response
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps

app = Flask(__name__)

APPLICATION_NAME = "Wolfgang Bike Exchange"
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///bikecatalog.db?check_same_thread=false')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect(url_for('LogMeIn'))
    return decorated_function


# Login flow
@app.route('/login')
def LogMeIn():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


# Gconnect Flow
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Login flow for Google OAuth """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if User exists, if not make new entry to db
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """
        " style = "width: 300px;
                        height: 300px;
                        border-radius: 150px;
                        -webkit-border-radius: 150px;
                        -moz-border-radius: 150px;"> """
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        email=login_session['email']).one_or_none()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
        return user.id
    except noUser:
        return None


# Disconnect Flow
@app.route('/gdisconnect')
def gdisconnect():
    """ Logout flow for Google OAuth """
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s' %
        login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON endpoint to display all models
@app.route('/model/JSON')
def modelsJSON():
    models = session.query(Model).all()
    return jsonify(models=[m.serialize for m in models])


# JSON endpoint to display all listings of a model
@app.route('/model/<string:model_name>/JSON')
def listingsJSON(model_name):
    model = session.query(Model).filter_by(name=model_name).one_or_none()
    listings = session.query(Bike).filter_by(type_id=model.id).all()
    return jsonify(bikes=[i.serialize for i in listings])


# JSON endpoint for a single listing
@app.route('/model/<string:model_name>/<string:listing_name>/JSON')
def bikeJSON(model_name, listing_name):
    thisBike = session.query(Bike).filter_by(name=listing_name).one_or_none()
    return jsonify(thisBike=thisBike.serialize)


# Landing page
@app.route('/')
def landingPage():
    return render_template('index.html')


# Show all models
@app.route('/explore/')
def showModels():
    models = session.query(Model).all()
    bikes = session.query(Bike).all()
    listings = session.query(Bike, Model).outerjoin(
        Model, Model.id == Bike.type_id).all()
    return render_template(
        'explore.html', models=models, bikes=bikes, listings=listings)

# @app.context_processor
# def id2Model(type_id):
#     model = session.query(Model).filter_by(id=type_id).one_or_none()
#     return model


# Create a new model
@app.route('/explore/model/new/', methods=['GET', 'POST'])
@login_required
def newModel():
    if request.method == 'POST':
        newModel = Model(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newModel)
        session.commit()
        return redirect(url_for('showModels'))
    else:
        return render_template('newModel.html')


# Edit a model
@app.route('/explore/model/<string:model_name>/edit/', methods=['GET', 'POST'])
@login_required
def editModel(model_name):
    editedModel = session.query(Model).filter_by(name=model_name).one_or_none()
    if editedModel.user_id != login_session['user_id']:
        return """<script>function alertfunc() {
            alert('You are not authorized to edit this bike model.');
            }</script><body onload='alertfunc()'>"""
    if request.method == 'POST':
        if request.form['name']:
            editedModel.name = request.form['name']
            return redirect(url_for('showModels'))
    else:
        return render_template('editModel.html', model=editedModel)


# Delete a model
@app.route(
    '/explore/model/<string:model_name>/delete/',
    methods=['GET', 'POST'])
@login_required
def deleteModel(model_name):
    modelToDelete = session.query(Model).filter_by(
        name=model_name).one_or_none()
    if modelToDelete.user_id != login_session['user_id']:
        return """<script>function alertfunc() {
        alert('You are not authorized to delete this bike model.');
        }</script><body onload='alertfunc()'>"""
    if request.method == 'POST':
        session.delete(modelToDelete)
        session.commit()
        return redirect(url_for('showModels', model_name=model_name))
    else:
        return render_template('deleteModel.html', model=modelToDelete)


# Show a model's listings
@app.route('/explore/model/<string:model_name>/')
def showBikes(model_name):
    models = session.query(Model).all()
    model = session.query(Model).filter_by(name=model_name).one_or_none()
    check = session.query(Bike).filter_by(type_id=model.id).first()
    if check is None:
        return render_template('emptyModel.html', model=model)
    else:
        listings = session.query(Bike).filter_by(type_id=model.id).all()
        return render_template(
            'listBikes.html', bikes=listings, model=model, models=models)


# Create a new listing
@app.route('/explore/model/<string:model_name>/new/', methods=['GET', 'POST'])
@login_required
def newBike(model_name):
    if request.method == 'POST':
        type = session.query(Model).filter_by(name=model_name).one_or_none()
        newBike = Bike(
            name=request.form['name'],
            description=request.form['desc'],
            price=request.form['price'],
            type_id=type.id,
            user_id=login_session['user_id'])
        session.add(newBike)
        session.commit()
        return redirect(url_for('showBikes', model_name=model_name))
    else:
        return render_template('newBike.html', model_name=model_name)


# View a listing
@app.route(
    '/explore/model/<string:model_name>/<string:listing_name>/',
    methods=['GET', 'POST'])
def thisBike(model_name, listing_name):
    models = session.query(Model).all()
    model = session.query(Model).filter_by(
        name=model_name).one_or_none()
    bike = session.query(Bike).filter_by(
        name=listing_name).one_or_none()

    return render_template(
        'viewBike.html', model=model, bike=bike, models=models)


# Edit a listing
@app.route(
    '/explore/model/<string:model_name>/<string:listing_name>/edit',
    methods=['GET', 'POST'])
@login_required
def editBike(model_name, listing_name):
    model = session.query(Model).filter_by(
        name=model_name).one_or_none()

    editedBike = session.query(Bike).filter_by(
        name=listing_name).one_or_none()

    if login_session['user_id'] != editedBike.user_id:
        return """<script>function alertfunc() {
        alert('You are not authorized to edit this bike listing.');
        }</script><body onload='alertfunc()'>"""

    if request.method == 'POST':
        if request.form['name']:
            editedBike.name = request.form['name']
        if request.form['desc']:
            editedBike.description = request.form['desc']
        if request.form['price']:
            editedBike.price = request.form['price']
        session.add(editedBike)
        session.commit()
        return redirect(
            url_for('thisBike',
                    model_name=model_name,
                    listing_name=editedBike.name))
    else:
        return render_template('editBike.html', bike=editedBike, model=model)


# Delete a listing
@app.route(
    '/explore/model/<string:model_name>/<string:listing_name>/delete',
    methods=['GET', 'POST'])
@login_required
def deleteBike(model_name, listing_name):
    model = session.query(Model).filter_by(
        name=model_name).one_or_none()

    delBike = session.query(Bike).filter_by(
        name=listing_name).one_or_none()

    if login_session['user_id'] != delBike.user_id:
        return """<script>function alertfunc() {
        alert('You are not authorized to delete this bike listing.');
        }</script><body onload='alertfunc()'>"""

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
