# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_login import UserMixin

from tagcam.database import Column, Model, SurrogatePK, db, reference_col, relationship
from tagcam.extensions import bcrypt


class Role(SurrogatePK, Model):
    """A role for a user."""

    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='roles')

    def __init__(self, name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Role({name})>'.format(name=self.name)


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = 'users'
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    #: The hashed password
    password = Column(db.Binary(128), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=False)
    is_admin = Column(db.Boolean(), default=False)

    def __init__(self, username, email, password=None, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, value):
        """Check password."""
        return bcrypt.check_password_hash(self.password, value)

    @property
    def full_name(self):
        """Full user name."""
        return '{0} {1}'.format(self.first_name, self.last_name)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User({username!r})>'.format(username=self.username)


class Tag(UserMixin, Model):
    """A user of the app."""

    __tablename__ = 'tags'
    username = Column(db.Integer, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    path = Column(db.String(1000), nullable=False)
    hash = Column(db.String(40), nullable=False)
    id = Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    # __table_args__ = {'extend_existing': True}

    tags = ['GISAXS', 'GIWAXS', 'SAXS', 'WAXS', 'AgB', 'Arc',
            'Isotropic', 'Peaks', 'Ring', 'Rod', 'Crystalline', 'Featureless']

    for tag in tags:
        locals()[tag] = Column(db.Boolean, default=False, nullable=False)

    def __init__(self, username, path, hash, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, path=path, hash=hash, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<Tag({path!r})>'.format(path=self.path)


class DataFile(Model):
    __tablename__ = 'datafiles'
    hash = Column(db.String(40), nullable=False, unique=True, primary_key=True)
    path = Column(db.String(1000), nullable=False, unique=True)
    tagged = Column(db.Integer, nullable=False, default=0)
    username = Column(db.Integer, nullable=False)
    __table_args__ = {'extend_existing': True}

    def __init__(self, hash, path, username, **kwargs):
        db.Model.__init__(self, hash=hash, path=path, username=username, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<DataFile({path!r})>'.format(path=self.path)
