from functools import wraps

from app import db

import logging

logger = logging.getLogger()


def commit_on_success(func):
    """Decorate any function to commit the session on success, rollback in
    the case of error.

    supports nested usage, committing only on the outermost nesting
    """
    @wraps(func)
    def commit_wrapper(*args, **kwargs):
        if hasattr( db.session, '__commit_on_success_active') and db.session.__commit_on_success_active:
            #don't mess with the commit
            return func(*args, **kwargs)

        db.session.__commit_on_success_active = True
        try:
            result = func(*args, **kwargs)
            db.session.commit()
        except Exception, e:
            db.session.rollback()
            logger.exception(u"Error occured in commit_on_success")
            db.session.__commit_on_success_active = False
            raise e
        else:
            db.session.__commit_on_success_active = False
            return result
    return commit_wrapper

# establish a constraint naming convention.
# see http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
#
db.metadata.naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s"
    }

def close_db(func):

    #closes the DB.  used for calls outside of flask, AKA celery

    @wraps(func)
    def wrapper(*args, **kwargs):
        if hasattr( db.session, '__close_db') and db.session.__close_db:
            #don't mess with the commit
            return func(*args, **kwargs)

        db.session.__close_db = True
        try:
            result = func(*args, **kwargs)
            db.session.close()
        except Exception, e:
            logger.exception(u"Error occurred closing db connection")
            db.session.__close_db = False
            raise e
        else:
            db.session.__close_db = False
            return result
    return wrapper
