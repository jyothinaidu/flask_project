import weakref
from sqlalchemy import Column, ForeignKeyConstraint

__author__ = 'james'

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy, Model
import config

app = Flask(__name__, static_folder='api/static', static_url_path='/static')
app.config.from_object(config)


class References(object):
    """A mixin which creates foreign key references to related classes."""
    _to_ref = set()
    _references = _to_ref.add

    @classmethod
    def __declare_first__(cls):
        """declarative hook called within the 'before_configure' mapper event."""
        for lcl, rmt in cls._to_ref:
            cls._decl_class_registry[lcl]._reference_table(
                    cls._decl_class_registry[rmt].__table__)
        cls._to_ref.clear()

    @classmethod
    def _reference_table(cls, ref_table):
        """Create a foreign key reference from the local class to the given remote
        table.

        Adds column references to the declarative class and adds a
        ForeignKeyConstraint.

        """
        # create pairs of (Foreign key column, primary key column)
        cols = [(Column(), refcol) for refcol in ref_table.primary_key]

        # set "tablename_colname =  Foreign key Column" on the local class
        for col, refcol in cols:
            setattr(cls, "%s_%s" % (ref_table.name, refcol.name), col)

        # add a ForeignKeyConstraint([local columns], [remote columns])
        cls.__table__.append_constraint(ForeignKeyConstraint(*zip(*cols)))

class MyModel(Model, References):
    pass


db = SQLAlchemy(app, model=MyModel)

from app.api.consumer_v1 import bp as blueprint
from app.api.courier_v1 import bp as courier_blueprint
from app.api.admin import bp as admin_blueprint
from app.api.retailer import bp as retailer_blueprint
app.register_blueprint(blueprint, url_prefix='/consumer/v1')
app.register_blueprint(courier_blueprint, url_prefix='/courier/v1')
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(retailer_blueprint, url_prefix='/retailer')

from custom_routes import CustomRoutes
CustomRoutes.init_custom_routes( app)


