from flask import Flask, redirect, request, url_for
from flask import Response

import requests

from flask import request
from flask import Flask, render_template

from jinja2 import Template
import secrets

import base64
import json
import os

from flask import session

app = Flask(__name__)

app.secret_key = secrets.token_hex()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, ForeignKey, String

from logging.config import dictConfig

dictConfig({
'version': 1,
'formatters': {'default': {
'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
}},
'handlers': {'wsgi': {
'class': 'logging.StreamHandler',
'stream': 'ext://flask.logging.wsgi_errors_stream',
'formatter': 'default'
},
'file.handler': {
'class': 'logging.handlers.RotatingFileHandler',
'filename': 'weatherportal.log',
'maxBytes': 10000000,
'backupCount': 5,
'level': 'DEBUG',
},
},
'root': {
'level': 'INFO',
'handlers': ['file.handler']
}
})

# SQLite Database creation
Base = declarative_base()
engine = create_engine("sqlite:///weatherportal.db", echo=True, future=True)
DBSession = sessionmaker(bind=engine)

@app.before_first_request
def create_tables():
    Base.metadata.create_all(engine)

class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<Admin %r>" % (self.name)

    # Ref: 
    def as_dict(self):
        fields = {}
        for c in self.__table__.columns:
            fields[c.name] = getattr(self, c.name)
        return fields

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<User %r>" % (self.name)

    def as_dict(self):
        fields = {}
        for c in self.__table__.columns:
            fields[c.name] = getattr(self, c.name)
        return fields

class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String)
    adminId = Column(Integer, ForeignKey('admin.id'))

    def __repr__(self):
        return "<City %r>" % (self.name)

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'adminId': self.adminId
        }

class UserCity(Base):
    __tablename__ = 'usercities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('users.id'))
    cityId = Column(Integer, ForeignKey('cities.id'))
    month = Column(String)
    year = Column(String)
    weather_params = Column(String)

    def __repr__(self):
        return "<UserCity %r>" % (self.id)

    def as_dict(self):
        return {
            'id': self.id,
            'userId': self.userId,
            'cityId': self.cityId,
            'month': self.month,
            'year': self.year,
            'weather_params': self.weather_params
        }


@app.route("/admin", methods=['POST'])
def add_admin():
    app.logger.info("Inside add_admin")
    data = request.json
    app.logger.info("Received request:%s", str(data))

    name = data['name']
    password = data['password']

    admin = Admin(name=name, password=password)

    db_session = DBSession()
    db_session.add(admin)
    db_session.commit()

    return admin.as_dict()

@app.route("/admin")
def get_admins():
    app.logger.info("Inside get_admins")
    ret_obj = {}

    db_session = DBSession()
    admins = db_session.query(Admin)
    admin_list = []
    for admin in admins:
        admin_list.append(admin.as_dict())

    ret_obj['admins'] = admin_list
    return ret_obj

@app.route("/admin/<int:id>")
def get_admin_by_id(id):
    app.logger.info("Inside get_admin_by_id %s\n", id)

    db_session = DBSession()
    admin = db_session.get(Admin, id)

    app.logger.info("Found admin:%s\n", str(admin))
    if admin == None:
        status = ("Admin with id {id} not found\n").format(id=id)
        return Response(status, status=404)
    else:
        return admin.as_dict()

@app.route("/admin/<int:id>", methods=['DELETE'])
def delete_admin_by_id(id):
    app.logger.info("Inside delete_admin_by_id %s\n", id)

    db_session = DBSession()
    admin = db_session.query(Admin).filter_by(id=id).first()

    app.logger.info("Found admin:%s\n", str(admin))
    if admin == None:
        status = ("Admin with id {id} not found.\n").format(id=id)
        return Response(status, status=404)
    else:
        db_session.delete(admin)
        db_session.commit()
        status = ("Admin with id {id} deleted.\n").format(id=id)
        return Response(status, status=200)

## Users REST API
@app.route("/users", methods=['POST'])
def add_user():
    app.logger.info("Inside add_user")
    data = request.json
    app.logger.info("Received request:%s", str(data))

    name = data['name']
    password = data['password']

    db_session = DBSession()
    existing = db_session.query(User).filter_by(name=name).first()
    if existing:
        status = ("User with {name} already exists.\n").format(name=name)
        return Response(status, status=400)

    user = User(name=name, password=password)
    db_session.add(user)
    db_session.commit()

    return user.as_dict()

@app.route("/users")
def get_users():
    app.logger.info("Inside get_users")
    ret_obj = {}

    db_session = DBSession()
    users = db_session.query(User)
    user_list = []
    for user in users:
        user_list.append(user.as_dict())

    ret_obj['users'] = user_list
    return ret_obj

@app.route("/users/<int:id>")
def get_user_by_id(id):
    app.logger.info("Inside get_user_by_id %s\n", id)

    db_session = DBSession()
    user = db_session.get(User, id)

    if user == None:
        status = ("User with id {id} not found.\n").format(id=id)
        return Response(status, status=404)
    else:
        return user.as_dict()

@app.route("/users/<int:id>", methods=['DELETE'])
def delete_user_by_id(id):
    app.logger.info("Inside delete_user_by_id %s\n", id)

    db_session = DBSession()
    user = db_session.query(User).filter_by(id=id).first()

    if user == None:
        status = ("User with id {id} not found.\n").format(id=id)
        return Response(status, status=404)
    else:
        db_session.delete(user)
        db_session.commit()
        status = ("User with id {id} deleted.\n").format(id=id)
        return Response(status, status=200)

## Admin Cities REST API
@app.route("/admin/<int:admin_id>/cities", methods=['POST'])
def add_city(admin_id):
    app.logger.info("Inside add_city")
    data = request.json
    app.logger.info("Received request:%s", str(data))

    db_session = DBSession()
    admin = db_session.get(Admin, admin_id)
    if admin == None:
        status = ("Admin with id {id} not found.\n").format(id=admin_id)
        return Response(status, status=404)

    name = data['name']
    url = data['url']

    city = City(name=name, url=url, adminId=admin_id)
    db_session.add(city)
    db_session.commit()

    return city.as_dict()

@app.route("/admin/<int:admin_id>/cities")
def get_cities(admin_id):
    app.logger.info("Inside get_cities")

    db_session = DBSession()
    admin = db_session.get(Admin, admin_id)
    if admin == None:
        status = ("Admin with id {id} not found.\n").format(id=admin_id)
        return Response(status, status=404)

    cities = db_session.query(City).filter_by(adminId=admin_id)
    city_list = []
    for city in cities:
        city_list.append(city.as_dict())

    return {'cities': city_list}

@app.route("/admin/<int:admin_id>/cities/<int:city_id>")
def get_city_by_id(admin_id, city_id):
    app.logger.info("Inside get_city_by_id %s\n", city_id)

    db_session = DBSession()
    admin = db_session.get(Admin, admin_id)
    if admin == None:
        status = ("Admin with id {id} not found.\n").format(id=admin_id)
        return Response(status, status=404)

    city = db_session.get(City, city_id)
    if city == None:
        status = ("City with id {id} not found.\n").format(id=city_id)
        return Response(status, status=404)

    return city.as_dict()

@app.route("/admin/<int:admin_id>/cities/<int:city_id>", methods=['DELETE'])
def delete_city_by_id(admin_id, city_id):
    app.logger.info("Inside delete_city_by_id %s\n", city_id)

    db_session = DBSession()
    admin = db_session.get(Admin, admin_id)
    if admin == None:
        status = ("Admin with id {id} not found.\n").format(id=admin_id)
        return Response(status, status=404)

    city = db_session.query(City).filter_by(id=city_id).first()
    if city == None:
        status = ("City with id {id} not found.\n").format(id=city_id)
        return Response(status, status=404)

    db_session.delete(city)
    db_session.commit()
    status = ("City with id {id} deleted.\n").format(id=city_id)
    return Response(status, status=200)

## User Cities REST API
@app.route("/users/<int:user_id>/cities", methods=['POST'])
def add_user_city(user_id):
    app.logger.info("Inside add_user_city")
    data = request.json
    app.logger.info("Received request:%s", str(data))

    db_session = DBSession()
    user = db_session.get(User, user_id)
    if user == None:
        status = ("User with id {id} not found.\n").format(id=user_id)
        return Response(status, status=404)

    city_name = data['name']
    city = db_session.query(City).filter_by(name=city_name).first()
    if city == None:
        status = ("City with name {name} not found.\n").format(name=city_name)
        return Response(status, status=404)

    year = str(data['year'])
    if len(year) != 4 or not year.isdigit():
        return Response("Year needs to be exactly four digits.\n", status=400)

    month = data['month']
    params = data['weather_params']

    user_city = UserCity(userId=user_id, cityId=city.id, month=month, year=year, weather_params=params)
    db_session.add(user_city)
    db_session.commit()

    return user_city.as_dict()

@app.route("/users/<int:user_id>/cities")
def get_user_cities(user_id):
    app.logger.info("Inside get_user_cities")

    db_session = DBSession()
    user = db_session.get(User, user_id)
    if user == None:
        status = ("User with id {id} not found.\n").format(id=user_id)
        return Response(status, status=404)

    city_name = request.args.get('name')

    if city_name:
        city = db_session.query(City).filter_by(name=city_name).first()
        if city == None:
            status = ("City with name {name} not found.\n").format(name=city_name)
            return Response(status, status=404)

        user_city = db_session.query(UserCity).filter_by(userId=user_id, cityId=city.id).first()
        if user_city == None:
            status = ("City with name {name} not being tracked by the user {uname}.\n").format(name=city_name, uname=user.name)
            return Response(status, status=404)

        return {
            'name': city_name,
            'month': user_city.month,
            'year': user_city.year,
            'weather_params': user_city.weather_params
        }

    user_cities = db_session.query(UserCity).filter_by(userId=user_id)
    uc_list = []
    for uc in user_cities:
        uc_list.append(uc.as_dict())

    return {'usercities': uc_list}

@app.route("/logout", methods=['GET'])
def logout():
    app.logger.info("Logout called.")
    session.pop('username', None)
    app.logger.info("Before returning...")
    return render_template('index.html')

@app.route("/login", methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    app.logger.info("Username:%s", username)
    app.logger.info("Password:%s", password)

    session['username'] = username

    return render_template('welcome.html',
        welcome_message = "Personal Weather Portal",
        cities=[],
        name=username,
        addButton_style="display:none;",
        addCityForm_style="display:none;",
        regButton_style="display:inline;",
        regForm_style="display:inline;",
        status_style="display:none;")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/adminlogin", methods=['POST'])
def adminlogin():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    app.logger.info("Username:%s", username)
    app.logger.info("Password:%s", password)

    session['username'] = username

    return render_template('welcome.html',
        welcome_message = "Personal Weather Portal - Admin Panel",
        cities=[],
        name=username,
        addButton_style="display:inline;",
        addCityForm_style="display:inline;",
        regButton_style="display:none;",
        regForm_style="display:none;",
        status_style="display:none;")

@app.route("/adminindex")
def adminindex():
    return render_template('adminindex.html')

if __name__ == "__main__":

    app.debug = False
    app.logger.info('Portal started...')
    app.run(host='0.0.0.0', port=5009)
