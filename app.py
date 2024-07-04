from flask import Flask, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os

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
    password = db.Column(db.String(80), nullable=False)
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

@app.route('/users/login', methods=['POST'])
def authenticate_user():
    data = request.json
    email = data['email']
    password = data['password']
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        return jsonify({"id": user.id, "first_name": user.first_name, "last_name": user.last_name})
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/files', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        user_id = request.form['user_id']
        title = request.form['title']
        description = request.form['description']
        keywords = request.form['keywords']
        course = request.form['course']
        file_type = file.filename.split('.')[-1].lower()
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        new_file = File(filename=filename, user_id=user_id, title=title, description=description, keywords=keywords, course=course, file_type=file_type)
        db.session.add(new_file)
        db.session.commit()
        return jsonify({"id": new_file.id, "filename": new_file.filename})

@app.route('/files', methods=['GET'])
def get_files():
    course = request.args.get('course', None)
    if course:
        files = File.query.filter_by(course=course).all()
    else:
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

def add_default_users():
    if not User.query.filter_by(email="angeles@mail.com").first():
        db.session.add(User(email="angeles@mail.com", password="1234", first_name="Angeles", last_name="Navarrete"))
    if not User.query.filter_by(email="simon@mail.com").first():
        db.session.add(User(email="simon@mail.com", password="1234", first_name="Simon", last_name="Mujica"))
    if not User.query.filter_by(email="diego@mail.com").first():
        db.session.add(User(email="diego@mail.com", password="1234", first_name="Diego", last_name="Hernandez"))
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_default_users()
    app.run(debug=True)
