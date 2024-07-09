from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apuntes.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(250), nullable=False)
    course = db.Column(db.String(120), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('files', lazy=True))

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    file = db.relationship('File', backref=db.backref('favorites', lazy=True))

@app.route('/api/saludo', methods=['GET'])
def saludo():
    return jsonify({"mensaje": "¡Hola desde el backend!"})

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.route('/users/login', methods=['POST'])
def authenticate_user():
    data = request.json
    email = data['email']
    password = data['password']
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return jsonify({"id": user.id, "first_name": user.first_name, "last_name": user.last_name})
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/users/google-login', methods=['POST'])
def google_login():
    data = request.json
    token = data.get('token')
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), "367342764631-tejhut1n7n3mls174d2ffmq86cdmf1ui.apps.googleusercontent.com")

        email = idinfo['email']
        first_name = idinfo['given_name']
        last_name = idinfo['family_name']

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, first_name=first_name, last_name=last_name)
            db.session.add(user)
            db.session.commit()

        return jsonify({"id": user.id, "first_name": user.first_name, "last_name": user.last_name})
    except ValueError:
        return jsonify({"error": "Invalid token"}), 400

@app.route('/users/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    
    if not email or not password or not first_name or not last_name:
        return jsonify({"error": "Missing fields"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 400
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(email=email, password=hashed_password, first_name=first_name, last_name=last_name)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        title = request.form.get('title')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        course = request.form.get('course')
        file_type = request.form.get('file_type')
        user_id = request.form.get('user_id')
        new_file = File(filename=filename, title=title, description=description, keywords=keywords, course=course, file_type=file_type, user_id=user_id)
        db.session.add(new_file)
        db.session.commit()
        return jsonify({"message": "File uploaded successfully"}), 201

@app.route('/files', methods=['GET'])
def get_files():
    files = File.query.all()
    file_list = [{"id": file.id, "filename": file.filename, "title": file.title, "description": file.description, "keywords": file.keywords, "course": file.course, "file_type": file.file_type, "user_id": file.user_id} for file in files]
    return jsonify({"files": file_list})

@app.route('/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    file = File.query.get(file_id)
    if not file:
        return jsonify({"error": "File not found"}), 404
    file_info = {"id": file.id, "filename": file.filename, "title": file.title, "description": file.description, "keywords": file.keywords, "course": file.course, "file_type": file.file_type, "user_id": file.user_id}
    return jsonify(file_info)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/favorites', methods=['POST'])
def add_favorite():
    data = request.json
    user_id = data['user_id']
    file_id = data['file_id']
    favorite = Favorite(user_id=user_id, file_id=file_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite added"})

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    favorite_files = [{"id": fav.file.id, "filename": fav.file.filename, "title": fav.file.title, "description": fav.file.description, "keywords": fav.file.keywords, "course": fav.file.course, "file_type": fav.file.file_type, "user_id": fav.file.user_id} for fav in favorites]
    return jsonify({"files": favorite_files})

@app.route('/users/<int:user_id>/files', methods=['GET'])
def get_user_files(user_id):
    files = File.query.filter_by(user_id=user_id).all()
    file_list = [{"id": file.id, "filename": file.filename, "title": file.title, "description": file.description, "keywords": file.keywords, "course": file.course, "file_type": file.file_type, "user_id": file.user_id} for file in files]
    return jsonify({"files": file_list})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
