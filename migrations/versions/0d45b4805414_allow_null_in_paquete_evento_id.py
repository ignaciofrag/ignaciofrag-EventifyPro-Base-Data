"""Allow NULL in paquete_evento_id

Revision ID: 0d45b4805414
Revises: 4d622add1ac5
Create Date: 2024-05-26 16:55:42.146534

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '0d45b4805414'
down_revision = '4d622add1ac5'
branch_labels = None
depends_on = None


def upgrade():
    # Obtener el inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Obtener las restricciones existentes en la tabla 'reservation'
    foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('reservation')]

    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.alter_column('paquete_evento_id',
               existing_type=sa.INTEGER(),
               nullable=True)

        # Intentar eliminar las restricciones solo si existen
        if 'reservation_paquete_evento_id_fkey' in foreign_keys:
            batch_op.drop_constraint('reservation_paquete_evento_id_fkey', type_='foreignkey')
        if 'reservation_proveedor_id_fkey' in foreign_keys:
            batch_op.drop_constraint('reservation_proveedor_id_fkey', type_='foreignkey')

        # Crear nuevas restricciones de clave foránea
        batch_op.create_foreign_key('reservation_paquete_evento_id_fkey', 'event_pack', ['paquete_evento_id'], ['id'])
        batch_op.create_foreign_key('reservation_proveedor_id_fkey', 'profile', ['proveedor_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # Obtener el inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Obtener las restricciones existentes en la tabla 'reservation'
    foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('reservation')]

    with op.batch_alter_table('reservation', schema=None) as batch_op:
        # Intentar eliminar las restricciones solo si existen
        if 'reservation_paquete_evento_id_fkey' in foreign_keys:
            batch_op.drop_constraint('reservation_paquete_evento_id_fkey', type_='foreignkey')
        if 'reservation_proveedor_id_fkey' in foreign_keys:
            batch_op.drop_constraint('reservation_proveedor_id_fkey', type_='foreignkey')

        # Crear las restricciones anteriores
        batch_op.create_foreign_key('reservation_proveedor_id_fkey', 'profile', ['paquete_evento_id'], ['id'])
        batch_op.create_foreign_key('reservation_paquete_evento_id_fkey', 'event_pack', ['proveedor_id'], ['id'])
        
        # Cambiar la columna para no permitir valores nulos
        batch_op.alter_column('paquete_evento_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
