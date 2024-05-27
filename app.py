from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from flask_cors import CORS
from models import db, User, Profile, Service, Event, Reservation, ReservationStatus
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from collections import OrderedDict
import pytz


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Configurar CORS
CORS(app, resources={r"/*": {"origins": "*"}})

def get_reservation_status_in_english(status):
    status_translation = {
        "Pendiente": "PENDING",
        "Confirmada": "CONFIRMED",
        "Cancelada": "CANCELLED",
        "Finalizada": "COMPLETED"
    }
    return status_translation.get(status, status)

def get_reservation_status_in_spanish(status):
    status_translation = {
        "PENDING": "Pendiente",
        "CONFIRMED": "Confirmada",
        "CANCELLED": "Cancelada",
        "COMPLETED": "Finalizada"
    }
    return status_translation.get(status, status)


################################## LOGIN ##################################
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

############################### REGISTRO ##################################
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

########################### OBTENER USUARIOS ##############################
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

@app.route('/user/me', methods=['GET'])
@jwt_required()
def get_user_info():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.profile.role
    }), 200

########################## ACTUALIZAR USUARIOS ############################
@app.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = db.session.get(User, user_id)
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
    user = db.session.get(User, user_id)
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

########################### SERVICIOS #####################################
@app.route('/services', methods=['POST'])
@jwt_required()
def add_service():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user.profile.role != 'Proveedor':
        return jsonify({"msg": "Unauthorized"}), 403
    data = request.json
    service = Service(
        name=data['name'],
        type=data['type'],
        price=data['price'],
        description=data['description'],
        location=data['location'],  # Añadir este campo
        profile_id=user.profile.id
    )
    db.session.add(service)
    db.session.commit()
    return jsonify({"msg": "Service added", "service_id": service.id}), 201

@app.route('/services', methods=['GET'])
def get_services():
    service_type = request.args.get('type', None)
    query = Service.query

    if service_type:
        query = query.filter(Service.type == service_type)

    services = query.all()
    services_list = []
    for service in services:
        profile = service.profile
        if profile:
            user = profile.user
            if user:
                services_list.append({
                    "id": service.id,
                    "name": service.name,
                    "type": service.type,
                    "price": service.price,
                    "description": service.description,
                    "location": service.location,
                    "provider_first_name": user.first_name,
                    "provider_last_name": user.last_name,
                    "company_name": profile.company_name,
                    "profile_id": profile.id,  # Añadir este campo
                    "created_at": service.created_at.isoformat()  # Asegúrate de que la fecha esté en formato ISO
                })
    return jsonify(services_list), 200

@app.route('/provider/<int:provider_id>/services', methods=['GET'])
@jwt_required()
def get_provider_services(provider_id):
    user_id_from_token = get_jwt_identity()
    user = db.session.get(User, user_id_from_token)
    if not user or user.profile.role != 'Proveedor' or user.id != provider_id:
        return jsonify({"msg": "Unauthorized"}), 403

    services = Service.query.filter_by(profile_id=user.profile.id).all()
    services_list = [{
        "id": service.id,
        "name": service.name,
        "type": service.type,
        "price": service.price,
        "description": service.description,
        "location": service.location
    } for service in services]
    return jsonify(services_list), 200

@app.route('/services/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"msg": "Service not found"}), 404
    if service.profile_id != user.profile.id:
        return jsonify({"msg": "Unauthorized"}), 403
    data = request.json
    service.name = data.get('name', service.name)
    service.type = data.get('type', service.type)
    service.price = data.get('price', service.price)
    service.description = data.get('description', service.description)
    service.location = data.get('location', service.location)  # Añadir este campo
    db.session.commit()
    return jsonify({"msg": "Service updated"}), 200

@app.route('/services/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"msg": "Service not found"}), 404
    if service.profile_id != user.profile.id:
        return jsonify({"msg": "Unauthorized"}), 403
    db.session.delete(service)
    db.session.commit()
    return jsonify({"msg": "Service deleted"}), 200

############### EVENTOS ##############################################
@app.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user.profile.role != 'Cliente':
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    required_fields = ['name', 'date', 'location', 'details', 'guests', 'eventype']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing field: {field}"}), 422

    try:
        madrid_timezone = pytz.timezone("Europe/Madrid")
        now_local = datetime.now(madrid_timezone)

        event = Event(
            name=data['name'],
            date=datetime.fromisoformat(data['date']),
            location=data['location'],
            details=data['details'],
            guests=data['guests'],
            eventype=data['eventype'],
            user_id=user_id,
            created_at=now_local  # Establecer la fecha y hora actuales en la zona horaria de Madrid
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({"msg": "Event created", "event_id": event.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creating event", "error": str(e)}), 500
    
@app.route('/events', methods=['GET'])
def get_all_events():
    madrid_timezone = pytz.timezone("Europe/Madrid")
    events = Event.query.all()
    return jsonify([{
        "id": event.id,
        "name": event.name,
        "date": event.date.isoformat(),
        "location": event.location,
        "eventype": event.eventype,
        "details": event.details,
        "guests": event.guests,
        "user_id": event.user_id,
        "created_at": event.created_at.astimezone(madrid_timezone).isoformat()  # Convertir a la zona horaria de Madrid
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

@app.route('/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    user_id = get_jwt_identity()
    event = db.session.get(Event, event_id)

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

@app.route('/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    user_id = get_jwt_identity()
    event = db.session.get(Event, event_id)

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
        madrid_timezone = pytz.timezone("Europe/Madrid")
        return jsonify({
            "msg": "Event updated",
            "event_id": event.id,
            "created_at": event.created_at.astimezone(madrid_timezone).isoformat()  # Convertir a la zona horaria de Madrid
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error updating event", "error": str(e)}), 500
    
    ############### RESERVAS ##############################################

# Crear una reserva
@app.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    user_id = get_jwt_identity()
    data = request.json

    required_fields = ['status', 'date_time_reservation', 'precio', 'proveedor_id', 'service_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"msg": f"Missing field: {field}"}), 422

    paquete_evento_id = data.get('paquete_evento_id', None)

    try:
        status_in_english = get_reservation_status_in_english(data['status'])
        if status_in_english not in ReservationStatus._member_names_:
            return jsonify({"msg": "Invalid status"}), 400

        reservation = Reservation(
            status=ReservationStatus[status_in_english],
            date_time_reservation=datetime.fromisoformat(data['date_time_reservation']),
            precio=data['precio'],
            proveedor_id=data['proveedor_id'],
            paquete_evento_id=paquete_evento_id,
            usuario_id=user_id,
            service_id=data['service_id'],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(reservation)
        db.session.commit()
        return jsonify({"msg": "Reservation created", "reservation_id": reservation.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error creating reservation: {str(e)}"}), 500

# Obtener todas las reservas
@app.route('/reservations', methods=['GET'])
@jwt_required()
def get_all_reservations():
    reservations = Reservation.query.all()
    reservations_list = [{
        "id": reservation.id,
        "status": reservation.status.name,  # Devuelve el nombre del estado en inglés
        "date_time_reservation": reservation.date_time_reservation.isoformat(),
        "precio": reservation.precio,
        "proveedor_id": reservation.proveedor_id,
        "paquete_evento_id": reservation.paquete_evento_id,
        "usuario_id": reservation.usuario_id,
        "service_id": reservation.service_id,
        "created_at": reservation.created_at.isoformat()
    } for reservation in reservations]
    return jsonify(reservations_list), 200

@app.route('/user/<int:user_id>/reservations', methods=['GET'])
@jwt_required()
def get_user_reservations(user_id):
    user_id_from_token = get_jwt_identity()
    if user_id_from_token != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    reservations = Reservation.query.filter_by(usuario_id=user_id).all()
    if not reservations:
        return jsonify([]), 200

    reservations_list = []
    for reservation in reservations:
        service = db.session.get(Service, reservation.service_id)
        provider_profile = db.session.get(Profile, service.profile_id)
        reservations_list.append({
            "id": reservation.id,
            "status": get_reservation_status_in_spanish(reservation.status.name),  # Traduce el estado al español
            "date_time_reservation": reservation.date_time_reservation.isoformat(),
            "precio": reservation.precio,
            "company_name": provider_profile.company_name,
            "email_contacto": provider_profile.user.email,
            "phone_number": provider_profile.phone_number,
            "address": provider_profile.address,
            "created_at": reservation.created_at.isoformat()
        })

    return jsonify(reservations_list), 200

#probando endpoint de GET 
@app.route('/provider/<int:provider_id>/reservations', methods=['GET'])
@jwt_required()
def get_provider_reservations(provider_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user.profile.role != 'Proveedor' or user.profile.id != provider_id:
        return jsonify({"msg": "Unauthorized"}), 403

    reservations = Reservation.query.filter_by(proveedor_id=provider_id).all()
    reservations_list = []
    for reservation in reservations:
        service = db.session.get(Service, reservation.service_id)
        client = db.session.get(User, reservation.usuario_id)
        reservations_list.append({
            "id": reservation.id,
            "status": get_reservation_status_in_spanish(reservation.status.name),
            "date_time_reservation": reservation.date_time_reservation.isoformat(),
            "precio": reservation.precio,
            "service_name": service.name,
            "client_name": f"{client.first_name} {client.last_name}",
            "client_email": client.email,
            "client_phone": client.profile.phone_number,
            "created_at": reservation.created_at.isoformat()
        })

    return jsonify(reservations_list), 200
# Obtener una reserva por ID
@app.route('/reservations/<int:reservation_id>', methods=['GET'])
@jwt_required()
def get_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    return jsonify({
        "id": reservation.id,
        "status": reservation.status.name,  # Devuelve el nombre del estado en inglés
        "date_time_reservation": reservation.date_time_reservation.isoformat(),
        "precio": reservation.precio,
        "proveedor_id": reservation.proveedor_id,
        "paquete_evento_id": reservation.paquete_evento_id,
        "usuario_id": reservation.usuario_id,
        "service_id": reservation.service_id,
        "created_at": reservation.created_at.isoformat()
    }), 200

# Actualizar una reserva
@app.route('/reservations/<int:reservation_id>', methods=['PUT'])
@jwt_required()
def update_reservation(reservation_id):
    data = request.json
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    try:
        new_status = data.get('status')
        if new_status and new_status not in ReservationStatus._member_names_:
            return jsonify({"msg": "Invalid status"}), 400

        if new_status:
            reservation.status = ReservationStatus[new_status]
        if 'date_time_reservation' in data:
            reservation.date_time_reservation = datetime.fromisoformat(data['date_time_reservation'])
        if 'precio' in data:
            reservation.precio = data['precio']
        if 'proveedor_id' in data:
            reservation.proveedor_id = data['proveedor_id']
        if 'paquete_evento_id' in data:
            reservation.paquete_evento_id = data['paquete_evento_id']
        if 'service_id' in data:
            reservation.service_id = data['service_id']
        db.session.commit()
        return jsonify({"msg": "Reservation updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error updating reservation: {str(e)}"}), 500

# Actualizar el estado de una reserva (solo para proveedores)
@app.route('/reservations/<int:reservation_id>/status', methods=['PATCH'])
@jwt_required()
def update_reservation_status(reservation_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user.profile.role != 'Proveedor':
        return jsonify({"msg": "Unauthorized"}), 403

    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    if reservation.proveedor_id != user.profile.id:
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.json
    try:
        new_status = data.get('status')
        if new_status not in ReservationStatus._member_names_:
            return jsonify({"msg": "Invalid status"}), 400

        reservation.status = ReservationStatus[new_status]
        db.session.commit()
        return jsonify({"msg": "Reservation status updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error updating reservation status: {str(e)}"}), 500

# Eliminar una reserva
@app.route('/reservations/<int:reservation_id>', methods=['DELETE'])
@jwt_required()
def delete_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    try:
        db.session.delete(reservation)
        db.session.commit()
        return jsonify({"msg": "Reservation deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error deleting reservation: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5500, debug=True)
