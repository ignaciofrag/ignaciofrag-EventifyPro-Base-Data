from app import app, db
from models import Reservation
from sqlalchemy.sql import text

def update_reservation_status():
    with app.app_context():
        # Actualizar los estados en la base de datos
        db.session.execute(
            text("UPDATE reservation SET status='PENDING' WHERE status='Pendiente'")
        )
        db.session.execute(
            text("UPDATE reservation SET status='CONFIRMED' WHERE status='Confirmada'")
        )
        db.session.execute(
            text("UPDATE reservation SET status='CANCELLED' WHERE status='Cancelada'")
        )
        db.session.execute(
            text("UPDATE reservation SET status='COMPLETED' WHERE status='Finalizada'")
        )
        db.session.commit()

if __name__ == "__main__":
    update_reservation_status()
    print("Reservation statuses updated successfully.")
