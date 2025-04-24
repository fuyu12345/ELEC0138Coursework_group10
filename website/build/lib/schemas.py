from src.model import Pasta, SalesRecord,User
from src import db, ma


# Flask-Marshmallow Schemas
class PastaSchema(ma.SQLAlchemyAutoSchema):
    """Marshmallow schema defining the attributes for creating a new pasta."""

    class Meta:
        model = Pasta
        
        load_instance = True
        sqla_session = db.session
        include_relationships = False


class SalesRecordSchema(ma.SQLAlchemyAutoSchema):
    """Marshmallow schema defining the attributes for creating a new sales record."""

    class Meta:
        model = SalesRecord
        include_fk = True
        load_instance = True
        sqla_session = db.session
        include_relationships = True


class UserSchema(ma.SQLAlchemySchema):
    """Marshmallow schema defining the attributes for creating a new user.

    The password_hash is set later using the
    """

    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session
        include_relationships = True

    email = ma.auto_field()
    password_hash = ma.auto_field()