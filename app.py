from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from flask_cors import CORS
from models import db, User, Profile, Message, Service, SupportTicket, EventPack, Media, Promotion, Reservation, Review, Event
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Cambiar esto por una clave más segura
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Configurar CORS
CORS(app)


@app.route('/user/login', methods=['POST'])
def login_user():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(email=email).first()
    if user and user.password == password:  # Aquí también debes considerar usar hashing para las contraseñas
        access_token = create_access_token(identity=user.id)
        user_info = {
            'id': user.id,
            'email': user.email,
            'role': user.profile.role,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        return jsonify(access_token=access_token, user=user_info), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

########################REGISTRO########################
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already exists"}), 409
    try:
        user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),  # Hasheada la contraseña con werkzeug
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        profile = Profile(
            user=user,
            phone_number=data['profile']['phone_number'],
            address=data['profile']['address'],
            description=data['profile']['description'],
            company_name=data['profile']['company_name'],
            url_portfolio=data['profile']['url_portfolio'],
            role=data['profile']['role']
        )
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()

        access_token = create_access_token(identity={'email': user.email, 'role': profile.role})

        return jsonify({"msg": "User created successfully", "user_id": user.id, "access_token": access_token}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error creating user: {str(e)}"}), 500

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


@app.route('/services', methods=['POST'])
@jwt_required()
def add_service():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.profile.role != 'provider':
        return jsonify({"msg": "Unauthorized"}), 403
    data = request.json
    service = Service(
        name=data['name'],
        type=data['type'],
        price=data['price'],
        description=data['description'],
        profile_id=user.profile.id
    )
    db.session.add(service)
    db.session.commit()
    return jsonify({"msg": "Service added", "service_id": service.id}), 201


@app.route('/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{
        "name": service.name,
        "type": service.type,
        "price": service.price,
        "description": service.description
    } for service in services]), 200


@app.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    try:
        data = request.json
        required_fields = ['status', 'date_time_reservation',
                           'price', 'provider_id', 'event_package_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Missing field: {field}"}), 422

        reservation = Reservation(
            status=data['status'],
            date_time_reservation=datetime.fromisoformat(
                data['date_time_reservation']),
            price=data['price'],
            provider_id=data['provider_id'],
            event_package_id=data['event_package_id'],
            user_id=get_jwt_identity()
        )
        db.session.add(reservation)
        db.session.commit()
        return jsonify({"msg": "Reservation created", "reservation_id": reservation.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creating reservation", "error": str(e)}), 500


@app.route('/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    user_id = get_jwt_identity()
    reservations = Reservation.query.filter_by(
        usuario_id=user_id).all()  # Usar usuario_id
    return jsonify([{
        "status": reservation.status,
        "date_time": reservation.date_time_reservation.isoformat(),
        "price": reservation.price,
        # Asegúrate de que este campo existe
        "guestCount": getattr(reservation, 'guest_count', 'N/A'),
        # Asegúrate de que este campo existe
        "name": getattr(reservation, 'name', 'N/A')
    } for reservation in reservations]), 200

############## EVENTOS###################


@app.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.profile.role != 'Cliente':
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    required_fields = ['name', 'date', 'location',
                       'details', 'guests', 'eventype']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing field: {field}"}), 422

    try:
        event = Event(
            name=data['name'],
            date=datetime.fromisoformat(data['date']),
            location=data['location'],
            details=data['details'],
            guests=data['guests'],
            eventype=data['eventype'],
            user_id=user_id
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({"msg": "Event created", "event_id": event.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creating event", "error": str(e)}), 500


@app.route('/events', methods=['GET'])
def get_all_events():
    events = Event.query.all()
    return jsonify([{
        "id": event.id,
        "name": event.name,
        "date": event.date.isoformat(),
        "location": event.location,
        "eventype": event.eventype,
        "details": event.details,
        "guests": event.guests,
        "user_id": event.user_id
    } for event in events]), 200


@app.route('/user/<int:user_id>/events', methods=['GET'])
@jwt_required()
def get_user_events(user_id):
    user_id_from_token = get_jwt_identity()
    if user_id_from_token != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    events = Event.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": event.id,
        "name": event.name,
        "date": event.date.isoformat(),
        "location": event.location,
        "details": event.details,
        "guests": event.guests,
        "eventype": event.eventype,
        "user_id": event.user_id
    } for event in events]), 200

        ###### DELETE######

@app.route('/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    user_id = get_jwt_identity()
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"msg": "Event not found"}), 404

    if event.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({"msg": "Event deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error deleting event", "error": str(e)}), 500

    
    ###### PUT######

@app.route('/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    user_id = get_jwt_identity()
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"msg": "Event not found"}), 404

    if event.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    allowed_fields = ['name', 'date', 'location',
                      'details', 'guests', 'eventype']

    for field in allowed_fields:
        if field in data:
            setattr(event, field, data[field] if field !=
                    'date' else datetime.fromisoformat(data[field]))

    try:
        db.session.commit()
        return jsonify({"msg": "Event updated", "event_id": event.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error updating event", "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5500, debug=True)
