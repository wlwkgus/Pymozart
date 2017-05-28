# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, url_for, redirect, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import reqparse, abort, Resource, Api
from functools import wraps
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import desc
from werkzeug.utils import secure_filename

import json
import os
import random


app = Flask(__name__)
api = Api(app)
app.config['UPLOAD_FOLDER'] = './static/images'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.secret_key = 'A'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

ADMIN_USERNAME = ''
ADMIN_PASSWORD = ''
BUCKET_NAME = ''
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
FILENAME_PREFIX = 'mozart_file_'
ARXIVNAME_PREFIX = 'arxiv_file_'

# SQLAlchemy json serialize class
class AlchemyEncoder(json.JSONEncoder):
	def default(self, obj):
	    if isinstance(obj.__class__, DeclarativeMeta):
	        # an SQLAlchemy class
	        fields = {}
	        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
	            data = obj.__getattribute__(field)
	            try:
	                json.dumps(data) # this will fail on non-encodable values, like other classes
	                fields[field] = data
	            except TypeError:
	                fields[field] = None
	        # a json-encodable dict
	        return fields

	    return json.JSONEncoder.default(self, obj)

# Model

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))

class Image(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	s3_key = db.Column(db.String(500))
	description = db.Column(db.String(500))

class Announcement(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String(500))
	text = db.Column(db.String(1000))
	image_link1 = db.Column(db.String(1000))
	image_link2 = db.Column(db.String(1000))
	file_link1 = db.Column(db.String(1000))
	file_link2 = db.Column(db.String(1000))

class Question(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(100))
	phone = db.Column(db.String(100))
	detail = db.Column(db.String(2000))

class ImageArchive(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	s3_key = db.Column(db.String(500))
	random_key = db.Column(db.String(100))


# decorators
def admin_only(func):
	@wraps(func)
	def func_wrapper(*args, **kwargs):
		if 'admin' in session:
			if session['admin'] == True:
				return func(*args, **kwargs)
		return 'you are not permitted'
	return func_wrapper

# functions
def jsonify_query(query_object):
	return json.loads(json.dumps(query_object, cls=AlchemyEncoder))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# APIView

class LoginView(Resource):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('username')
		parser.add_argument('password')
		args = parser.parse_args()
		if args['username'] == ADMIN_USERNAME and args['password'] == ADMIN_PASSWORD:
			session['admin'] = True
			return redirect(url_for('admin'))
		else:
			return 0

class LogoutView(Resource):
	def get(self):
		session['admin'] = False
		return 'logout success'

class ImageListView(Resource):
	def get(self):
		return jsonify_query(Image.query.order_by(desc(Image.id)).limit(10).all())

class ImageArxivListView(Resource):
	def get(self):
		return jsonify_query(ImageArchive.query.order_by(desc(ImageArchive.id)).limit(10).all())

class ImageView(Resource):
	@admin_only
	def delete(self, image_id):
		image = Image.query.get(image_id)
		try:
			try:
				os.remove(os.getcwd() + '/static/images/' + image.s3_key)
			except:
				pass
			db.session.delete(image)
			db.session.commit()
			return '1'
		except:
			# raise
			return '0'

class QuestionListView(Resource):
	@admin_only
	def get(self):
		return jsonify_query(Question.query.order_by(desc(Question.id)).limit(10).all())

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('name')
		parser.add_argument('phone')
		parser.add_argument('detail')
		args = parser.parse_args()
		try:
			if not args['name'] or not args['phone'] or not args['detail']:
				return '0'
			db.session.add(Question(name=args['name'], phone=args['phone'], detail=args['detail']))
			db.session.commit()
			return '1'
		except:
			return '99'

class QuestionView(Resource):
	@admin_only
	def delete(self, question_id):
		question = Question.query.get(question_id)
		try:
			db.session.delete(question)
			db.session.commit()
			return '1'
		except:
			return '0'

class AnnouncementListView(Resource):
	def get(self):
		return jsonify_query(Announcement.query.order_by(desc(Announcement.id)).limit(5).all())

	@admin_only
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('title')
		parser.add_argument('text')
		parser.add_argument('image_link1')
		parser.add_argument('image_link2')
		parser.add_argument('file_link1')
		parser.add_argument('file_link2')
		args = parser.parse_args()
		try:
			db.session.add(Announcement(
				title=args['title'],
				text=args['text'],
				image_link1=args['image_link1'],
				image_link2=args['image_link2'],
				file_link1=args['file_link1'],
				file_link2=args['file_link2']
				)
			)
			db.session.commit()
			return '1'
		except:
			return '99'

class AnnouncementView(Resource):
	@admin_only
	def delete(self, announcement_id):
		announcement = Announcement.query.get(announcement_id)
		try:
			db.session.delete(announcement)
			db.session.commit()
			return '1'
		except:
			return '0'



# Routing
@app.route('/')
def home():
	return render_template('index.html')

@app.route('/login')
def login():
	if 'admin' in session:
		if session['admin'] == True:
			return 'You already logined!'
	return render_template('login.html')

@app.route('/admin')
@admin_only
def admin():
	return render_template('admin.html')

@app.route('/admin/image')
@admin_only
def image():
	return render_template('image.html')

@app.route('/admin/image_arxiv')
@admin_only
def image_arxiv():
	return render_template('image_arxiv.html')

@app.route('/admin/image/create')
@admin_only
def create_image():
	return render_template('image_create.html')

@app.route('/admin/image_arxiv/create')
@admin_only
def create_image_arxiv():
	return render_template('image_arxiv_create.html')

@app.route('/admin/announcement')
@admin_only
def announcement():
	return render_template('announcement.html')

@app.route('/admin/announcement/create')
@admin_only
def create_announcement():
	return render_template('announcement_create.html')

@app.route('/admin/question')
@admin_only
def question():
	return render_template('question.html')

@app.route('/image', methods=['POST'])
@admin_only
def image_upload():
	if 'image' not in request.files:
		return 'No file'
	image = request.files['image']
	description = request.form['description']
	image_object = Image(description=description)
	db.session.add(image_object)
	db.session.commit()
	image_object = Image.query.filter_by(description=description).first()
	save_filename = FILENAME_PREFIX + str(image_object.id) + '.' + image.filename.split('.')[-1]
	image_object.s3_key = save_filename
	# if user does not select file, browser also
	# submit a empty part without filename
	if image.filename == '':
		return 'No selected file'
	if image and allowed_file(image.filename):
		image.save(os.path.join(app.config['UPLOAD_FOLDER'], save_filename))
		db.session.commit()
		return redirect(url_for('image'))

@app.route('/image_arxiv', methods=['POST'])
@admin_only
def image_arxiv_upload():
	if 'image' not in request.files:
		return 'No file'
	image = request.files['image']
	str_list = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
	random_key = ''
	for i in range(random.randint(3, 10)):
		random_key += str_list[random.randint(0, len(str_list) - 1)]
	image_object = ImageArchive(random_key=random_key)
	db.session.add(image_object)
	db.session.commit()
	image_object = Image.query.filter_by(random_key=random_key).first()
	save_filename = ARXIVNAME_PREFIX + str(image_object.id) + '.' + image.filename.split('.')[-1]
	image_object.s3_key = save_filename
	# if user does not select file, browser also
	# submit a empty part without filename
	if image.filename == '':
		return 'No selected file'
	if image and allowed_file(image.filename):
		image.save(os.path.join(app.config['UPLOAD_FOLDER'], save_filename))
		db.session.commit()
		return redirect(url_for('image_arxiv'))

@app.route('/image_get/<filename>')
def image_get(filename):
	return send_file(app.config['UPLOAD_FOLDER'][2:] + '/' +  filename)

@app.route('/image_arxiv_get/<filename>')
def image_arxiv_get(filename):
	return send_file(app.config['UPLOAD_FOLDER'][2:] + '/' +  filename)

# REST API
api.add_resource(LoginView, '/login')
api.add_resource(ImageListView, '/image')
api.add_resource(ImageArxivListView, '/image_arxiv')
api.add_resource(ImageView, '/image/<image_id>')
api.add_resource(LogoutView, '/logout')
api.add_resource(AnnouncementListView, '/announcement')
api.add_resource(AnnouncementView, '/announcement/<announcement_id>')
api.add_resource(QuestionListView, '/question')
api.add_resource(QuestionView, '/question/<question_id>')

if __name__=='__main__':
	app.run(debug=True, host='0.0.0.0')
