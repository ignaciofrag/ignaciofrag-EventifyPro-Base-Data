from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    profile = db.relationship('Profile', backref='user', uselist=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    tickets = db.relationship('SupportTicket', backref='user')
    reviews = db.relationship('Review', backref='user')#***********

class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(50))
    address = db.Column(db.String(200))
    description = db.Column(db.Text)
    company_name = db.Column(db.String(200), nullable=True)  # Opcional
    url_portfolio = db.Column(db.String(200))
    role = db.Column(db.String(50))
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    services = db.relationship('Service', backref='profile')

    # Especificar las llaves foráneas para evitar ambigüedades en las relaciones
    messages_sent = db.relationship(
        'Message',
        foreign_keys='[Message.client_id]',
        backref=db.backref('client', lazy='joined')
    )
    messages_received = db.relationship(
        'Message',
        foreign_keys='[Message.provider_id]',
        backref=db.backref('provider', lazy='joined')
    )
    event_packs = db.relationship('EventPack', backref='profile')
    reservations = db.relationship('Reservation', backref='profile')
class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    reviews = db.relationship('Review', backref='service')
    media = db.relationship('Media', backref='service')

class SupportTicket(db.Model):
    __tablename__ = 'support_ticket'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class EventPack(db.Model):
    __tablename__ = 'event_pack'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float)
    provider_id = db.Column(db.Integer, db.ForeignKey('profile.id'))

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))

class Promotion(db.Model):
    __tablename__ = 'promotion'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    price = db.Column(db.Float)
    provider_id = db.Column(db.Integer, db.ForeignKey('profile.id'))

class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    date_time_reservation = db.Column(db.DateTime)
    precio = db.Column(db.Float)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('event_pack.id'))
    paquete_evento_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime)
    provider_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    score = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))

    #test