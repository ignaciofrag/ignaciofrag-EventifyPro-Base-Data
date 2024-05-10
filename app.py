from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, User, Profile, Message, Service, SupportTicket, EventPack, Media, Promotion, Reservation, Review
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app, supports_credentials=True)
# Configuración de CORS mejorada
print("CORS configurado correctamente")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    user_data = {
        'id': user.id,
        'email': user.email,
        'profile': {
            'phone_number': user.profile.phone_number if user.profile else None,
            'address': user.profile.address if user.profile else None,
            'description': user.profile.description if user.profile else None,
            'company_name': user.profile.company_name if user.profile else None,
            'url_portfolio': user.profile.url_portfolio if user.profile else None,
            'role': user.profile.role if user.profile else None
        } if user.profile else {}
    }
    return jsonify(user_data), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    users_list = [{
        'id': user.id,
        'email': user.email,
        'profile': {
            'phone_number': user.profile.phone_number if user.profile else None,
            'address': user.profile.address if user.profile else None,
            'description': user.profile.description if user.profile else None,
            'company_name': user.profile.company_name if user.profile else None,
            'url_portfolio': user.profile.url_portfolio if user.profile else None,
            'role': user.profile.role if user.profile else None
        } if user.profile else {}
    } for user in users]
    return jsonify(users_list), 200

@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    if not data or 'email' not in data or 'password' not in data or 'first_name' not in data or 'last_name' not in data:
        return jsonify({'message': 'Datos insuficientes para la creación del usuario'}), 400
    
    try:
        user = User(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        db.session.add(user)
        db.session.flush()  # Obtener el ID antes de commit para usarlo en el perfil

        if 'profile' in data:
            profile_data = data['profile']
            profile = Profile(
                usuario_id=user.id,
                phone_number=profile_data.get('phone_number'),
                address=profile_data.get('address'),
                description=profile_data.get('description'),
                company_name=profile_data.get('company_name'),
                url_portfolio=profile_data.get('url_portfolio'),
                role=profile_data.get('role')
            )
            db.session.add(profile)
        
        db.session.commit()
        return jsonify({'message': 'Usuario y perfil creados exitosamente', 'id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")  # Agregar impresión del error
        return jsonify({'message': 'Error al crear el usuario', 'error': str(e)}), 500
    

@app.route('/user/login', methods=['POST'])
def login_user():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password == data['password']:
        user_info = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.profile.role  # cliente o proveedor

            # Añade otros campos necesarios aquí
        }
        return jsonify({'message': 'Login exitoso', 'user': user_info}), 200
    else:
        return jsonify({'message': 'Credenciales incorrectas'}), 401

    # Actualizar los datos del usuario
@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    data = request.json
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    if 'password' in data and data['password']:
        user.password = data['password']  # Consideremos hashing de contraseña italo
    if 'profile' in data:
        profile = user.profile
        if profile:
            profile.phone_number = data['profile'].get('phone_number', profile.phone_number)
            profile.address = data['profile'].get('address', profile.address)
            profile.description = data['profile'].get('description', profile.description)
            profile.company_name = data['profile'].get('company_name', profile.company_name)
            profile.url_portfolio = data['profile'].get('url_portfolio', profile.url_portfolio)
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
    }), 200

if __name__ == '__main__':
    app.run(host='localhost', port=5500, debug=True)
