from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json
from models import db, User, Profile, Message, Service, SupportTicket, EventPack, Media, Promotion, Reservation, Review

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(120))
    description = db.Column(db.Text)
    company_name = db.Column(db.String(120))
    url_portfolio = db.Column(db.String(255))
    role = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('profiles', lazy=True))

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    return jsonify({'id': user.id, 'email': user.email})

@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Usuario creado exitosamente'}), 201

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    data = request.json
    user.password = data.get('password', user.password)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({'message': 'Usuario actualizado exitosamente'}), 200

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuario eliminado exitosamente'}), 200

@app.route('/profile/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'message': 'Perfil no encontrado'}), 404
    return jsonify({
        'id': profile.id,
        'phone_number': profile.phone_number,
        'address': profile.address,
        'description': profile.description,
        'company_name': profile.company_name,
        'url_portfolio': profile.url_portfolio,
        'role': profile.role,
        'user_id': profile.user_id
    })

@app.route('/profile', methods=['POST'])
def create_profile():
    data = request.json
    profile = Profile(**data)
    db.session.add(profile)
    db.session.commit()
    return jsonify({'message': 'Perfil creado exitosamente'}), 201

@app.route('/profile/<int:profile_id>', methods=['PUT'])
def update_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'message': 'Perfil no encontrado'}), 404
    data = request.json
    profile.phone_number = data.get('phone_number', profile.phone_number)
    profile.address = data.get('address', profile.address)
    profile.description = data.get('description', profile.description)
    profile.company_name = data.get('company_name', profile.company_name)
    profile.url_portfolio = data.get('url_portfolio', profile.url_portfolio)
    profile.role = data.get('role', profile.role)
    db.session.commit()
    return jsonify({'message': 'Perfil actualizado exitosamente'}), 200

@app.route('/profile/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'message': 'Perfil no encontrado'}), 404
    db.session.delete(profile)
    db.session.commit()
    return jsonify({'message': 'Perfil eliminado exitosamente'}), 200

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)