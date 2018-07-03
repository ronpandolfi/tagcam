# -*- coding: utf-8 -*-
"""User forms."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, RadioField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask import url_for
import os

from .models import User, DataFile, db, Tag
import imageio
import fabio
import numpy as np
import hashlib
from sqlalchemy.sql.expression import func, select
from matplotlib import pyplot as plt

from skimage.transform import resize


class RegisterForm(FlaskForm):
    """Register form."""

    username = StringField('Username',
                           validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(min=6, max=40)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Verify password',
                            [DataRequired(), EqualTo('password', message='Passwords must match')])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already registered')
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False
        return True


class TagForm(FlaskForm):
    """Tag form."""
    # saxs = BooleanField(label='SAXS')
    # gisaxs = BooleanField(label='GISAXS')
    # tag = RadioField(label='Tags', choices=[(name, name) for name in Tag.tags])
    tags = {}
    hash = HiddenField(label='hash')
    path = HiddenField(label='path')

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(TagForm, self).__init__(*args, **kwargs)

        session = db.session  # type: db.Session
        datafile = session.query(DataFile).filter(DataFile.tagged < 2).order_by(func.random()).limit(1).first()

        if not datafile:
            return

        framepath = datafile.path
        self.path.data = framepath
        data = fabio.open(framepath).data
        self.hash.data = datafile.hash
        data = np.nan_to_num(np.log(data))

        clip = np.percentile(data, 99.9)
        data[data > clip] = clip

        floor = np.percentile(data[data > 0], 1)
        data[data < 0] = 0
        data = ((data - floor) / (data.max() - floor) * 255)
        data[data < 0] = 0
        data = data.astype(np.uint8)
        colordata = plt.cm.viridis(data)[:, :, :3]

        if not os.path.isfile(f'{self.hash.data}.jpg'):
            imageio.imwrite(os.path.join('tagcam/', 'static/', f'{self.hash.data}.jpg'), colordata)

        if not os.path.isfile(f'{self.hash.data}_256.tif'):
            rescaled = resize(data, (256, 256))
            imageio.imwrite(os.path.join('training/', '256/', f'{self.hash.data}.tif'), rescaled)

        if not os.path.isfile(f'{self.hash.data}_128.tif'):
            rescaled = resize(data, (128, 128))
            imageio.imwrite(os.path.join('training/', '128/', f'{self.hash.data}.tif'), rescaled)

    def validate(self):
        """Validate the form."""
        return True

    def get_jpg_data(self):
        return url_for('static', filename=f'{self.hash.data}.jpg')


for tag, description in Tag.tags.items():
    field = BooleanField(label=tag, description=description)
    setattr(TagForm, tag, field)
    TagForm.tags[tag] = description


class ImportDataForm(FlaskForm):
    """ Form for importing data files """
    path = StringField(label='Path')

    def validate(self):
        if not os.path.isdir(self.path.data):
            if self.path.errors:
                self.path.errors = tuple(list(self.path.errors).append('This path does not exist.'))
            else:
                self.path.errors = ('This path does not exist.',)
            return False
        return True
