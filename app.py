from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from flask_cors import CORS
from models import db, User, Profile, Message, Service, SupportTicket, EventPack, Media, Promotion, Reservation, Review, Event
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict



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

##################################LOGIN################################################################
@app.route('/user/login', methods=['POST'])
def login_user():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        user_info = {
            'id': user.id,
            'email': user.email,
            'role': user.profile.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': {
                'phone_number': user.profile.phone_number,
                'address': user.profile.address,
                'description': user.profile.description,
                'company_name': user.profile.company_name,
                'url_portfolio': user.profile.url_portfolio,
                'role': user.profile.role
            }
        }
        return jsonify(access_token=access_token, user=user_info), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

############################### REGISTRO #########################################
@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already exists"}), 409
    try:
        user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
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

        access_token = create_access_token(identity=user.id)
        user_info = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': {
                'phone_number': profile.phone_number,
                'address': profile.address,
                'description': profile.description,
                'company_name': profile.company_name,
                'url_portfolio': profile.url_portfolio,
                'role': profile.role
            }
        }

        return jsonify({"msg": "User created successfully", "user": user_info, "access_token": access_token}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error creating user: {str(e)}"}), 500
    

    ##############################GOOGLE REGISTRO################################################

    

#############################OBETENER USUARIOS################################################################
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    users_list = [OrderedDict([
        ('id', user.id),
        ('first_name', user.first_name),
        ('last_name', user.last_name),
        ('email', user.email),
        ('profile', {
            'phone_number': user.profile.phone_number if user.profile else None,
            'address': user.profile.address if user.profile else None,
            'description': user.profile.description if user.profile else None,
            'company_name': user.profile.company_name if user.profile else None,
            'url_portfolio': user.profile.url_portfolio if user.profile else None,
            'role': user.profile.role if user.profile else None
        } if user.profile else {})
    ]) for user in users]
    return jsonify(users_list), 200

##################################################ACTUALIZAR USUARIOS################################################
@app.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "profile": {
            "phone_number": user.profile.phone_number,
            "company_name": user.profile.company_name,
            "url_portfolio": user.profile.url_portfolio,
            "role": user.profile.role
        }
    }), 200

@app.route('/user/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    try:
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)

        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')

        if current_password and not check_password_hash(user.password, current_password):
            return jsonify({"msg": "Contraseña actual incorrecta"}), 400

        if new_password and new_password == confirm_password:
            user.password = generate_password_hash(new_password)
        elif new_password:
            return jsonify({"msg": "Las nuevas contraseñas no coinciden"}), 400

        if 'profile' in data:
            user.profile.phone_number = data['profile'].get('phone_number', user.profile.phone_number)
            user.profile.company_name = data['profile'].get('company_name', user.profile.company_name)
            user.profile.url_portfolio = data['profile'].get('url_portfolio', user.profile.url_portfolio)
            user.profile.role = data['profile'].get('role', user.profile.role)

        db.session.commit()
        return jsonify({"msg": "User updated successfully", "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "profile": {
                "phone_number": user.profile.phone_number,
                "company_name": user.profile.company_name,
                "url_portfolio": user.profile.url_portfolio,
                "role": user.profile.role
            }
        }}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error updating user: {str(e)}"}), 500

###########################SERVICIOS###############################################################################
@app.route('/services', methods=['POST'])
@jwt_required()
def add_service():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user.profile.role != 'Proveedor':
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
        "id": service.id,
        "name": service.name,
        "type": service.type,
        "price": service.price,
        "description": service.description
    } for service in services]), 200

@app.route('/services/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"msg": "Service not found"}), 404
    if service.profile_id != user.profile.id:
        return jsonify({"msg": "Unauthorized"}), 403
    data = request.json
    service.name = data.get('name', service.name)
    service.type = data.get('type', service.type)
    service.price = data.get('price', service.price)
    service.description = data.get('description', service.description)
    db.session.commit()
    return jsonify({"msg": "Service updated"}), 200

@app.route('/services/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"msg": "Service not found"}), 404
    if service.profile_id != user.profile.id:
        return jsonify({"msg": "Unauthorized"}), 403
    db.session.delete(service)
    db.session.commit()
    return jsonify({"msg": "Service deleted"}), 200

############################################################
@app.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    try:
        data = request.json
        required_fields = ['status', 'date_time_reservation', 'price', 'provider_id', 'event_package_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Missing field: {field}"}), 422

        reservation = Reservation(
            status=data['status'],
            date_time_reservation=datetime.fromisoformat(data['date_time_reservation']),
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
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": reservation.id,
        "status": reservation.status,
        "date_time_reservation": reservation.date_time_reservation.isoformat(),
        "price": reservation.price,
        "provider_id": reservation.provider_id,
        "event_package_id": reservation.event_package_id
    } for reservation in reservations]), 200

@app.route('/reservations/<int:reservation_id>', methods=['PUT'])
@jwt_required()
def update_reservation(reservation_id):
    try:
        user_id = get_jwt_identity()
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({"msg": "Reservation not found"}), 404
        if reservation.user_id != user_id:
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.json
        reservation.status = data.get('status', reservation.status)
        reservation.date_time_reservation = datetime.fromisoformat(data['date_time_reservation']) if 'date_time_reservation' in data else reservation.date_time_reservation
        reservation.price = data.get('price', reservation.price)
        reservation.provider_id = data.get('provider_id', reservation.provider_id)
        reservation.event_package_id = data.get('event_package_id', reservation.event_package_id)
        db.session.commit()
        return jsonify({"msg": "Reservation updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error updating reservation", "error": str(e)}), 500

@app.route('/reservations/<int:reservation_id>', methods=['DELETE'])
@jwt_required()
def delete_reservation(reservation_id):
    try:
        user_id = get_jwt_identity()
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({"msg": "Reservation not found"}), 404
        if reservation.user_id != user_id:
            return jsonify({"msg": "Unauthorized"}), 403

        db.session.delete(reservation)
        db.session.commit()
        return jsonify({"msg": "Reservation deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error deleting reservation", "error": str(e)}), 500

############## EVENTOS#######################################################################


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
    if not events:
        return jsonify([]), 200

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
    allowed_fields = ['name', 'date', 'location', 'details', 'guests', 'eventype']

    for field in allowed_fields:
        if field in data:
            setattr(event, field, data[field] if field != 'date' else datetime.fromisoformat(data[field]))

    try:
        db.session.commit()
        return jsonify({"msg": "Event updated", "event_id": event.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error updating event", "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5500, debug=True)
