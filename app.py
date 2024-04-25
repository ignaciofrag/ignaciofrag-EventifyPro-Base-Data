from flask import Flask
from flask_migrate import Migrate
from models import db, User, Profile, Message, Service, SupportTicket, EventPack, Media, Promotion, Reservation, Review

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
Migrate(app, db)

if __name__ == "__main__":
    app.run(host='localhost', port=5000)