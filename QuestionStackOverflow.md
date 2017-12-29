Hi,

I am new-ish to sqlalchemy and would like to use Flask-SQLAchemy toolkit with Flask, which I am doing in currently.

However, the issue is I have an issue where it seems that using a Base class subclassed from the zzzeek example:

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

            # set "tablename_colname = Foreign key Column" on the local class
            for col, refcol in cols:
                setattr(cls, "%s_%s" % (ref_table.name, refcol.name), col)

            # add a ForeignKeyConstraint([local columns], [remote columns])
            cls.__table__.append_constraint(ForeignKeyConstraint(*zip(*cols)))


class Base(References):
    pass


Base = declarative_base(...., cls=Base)


I hit a snag at Flask application config and creation time whereby all my dictionary objects aren't in place when I
want to instantiate the SQLAlchemy(....) class since all my classes that "inheret" from db.Model aren't present in the
cls._declr_class_registery on line 15.

This is the stack track.

    Traceback (most recent call last):
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/shell.py", line 10, in <module>
        from app import *
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/__init__.py", line 72, in <module>
        from app.api.consumer_v1 import bp as blueprint
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/api/__init__.py", line 4, in <module>
        import courier_v1
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/api/courier_v1/__init__.py", line 5, in <module>
        from .routes import routes
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/api/courier_v1/routes.py", line 10, in <module>
        from .api.cards import Cards
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/api/courier_v1/api/__init__.py", line 5, in <module>
        import app.ops
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/ops/__init__.py", line 3, in <module>
        from requesthandler import consumer_request_handle
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/ops/requesthandler.py", line 1, in <module>
        from app.ops.consumer_operations import consumer_operations, ConsumerOpFactory
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/ops/consumer_operations.py", line 13, in <module>
        from app.users.serialize import ApplicationInstallationSchema, UserAddressSchema, ConsumerUserSchema, CourierUserSchema
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/users/serialize.py", line 11, in <module>
        class AuthSessionSchema(ModelSchema):
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/marshmallow/schema.py", line 116, in __new__
        dict_cls=dict_cls
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/marshmallow_sqlalchemy/schema.py", line 59, in get_declared_fields
        fields=opts.fields,
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/marshmallow_sqlalchemy/convert.py", line 53, in fields_for_model
        for prop in model.__mapper__.iterate_properties:
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/sqlalchemy/orm/mapper.py", line 1819, in iterate_properties
        configure_mappers()
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/sqlalchemy/orm/mapper.py", line 2704, in configure_mappers
        Mapper.dispatch._for_class(Mapper).before_configured()
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/sqlalchemy/event/attr.py", line 218, in __call__
        fn(*args, **kw)
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/sqlalchemy/orm/events.py", line 550, in wrap
        fn(*arg, **kw)
      File "/Users/james/.virtualenvs/trustmile-api/lib/python2.7/site-packages/sqlalchemy/ext/declarative/base.py", line 149, in before_configured
        self.cls.__declare_first__()
      File "/Users/james/Documents/workspace/trustmile-backend/trustmile/app/__init__.py", line 30, in __declare_first__
        cls._decl_class_registry[lcl]._reference_table(
      File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/weakref.py", line 70, in __getitem__
        o = self.data[key]()
    KeyError: 'Card'
