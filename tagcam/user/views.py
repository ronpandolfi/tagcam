# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, make_response, flash, session, redirect, url_for
from tagcam.utils import flash_errors
from flask_login import login_required
from .forms import TagForm, ImportDataForm
from tagcam.user.models import Tag, DataFile, db
from sqlalchemy.sql import exists
import os
import glob
import fabio
import hashlib


blueprint = Blueprint('user', __name__, url_prefix='/users', static_folder='../static')


@blueprint.route('/')
@login_required
def members():
    """List members."""
    return redirect(url_for('user.tag'))


@blueprint.route('/tag/', methods=['GET', 'POST'])
@login_required
def tag():
    """Tag an image."""
    form = TagForm()
    print('dir:',dir(form))
    if form.validate_on_submit():

        newtag = Tag(hash=form.hash.data,
                     path=form.path.data,
                     username=session["user_id"],
                     **{taglabel: getattr(form, taglabel).data for taglabel in form.tags},
                     )
        newtag.save()

        datafile = db.session.query(DataFile).filter_by(hash=form.hash.data).first()
        datafile.tagged += 1

        db.session.commit()

        tags = ', '.join([taglabel for taglabel in form.tags if getattr(form, taglabel).data])
        if tags:
            flash(f'Image tagged with {tags}!', 'success')

    else:
        flash_errors(form)
    return render_template('users/tag.html', form=form)


@blueprint.route('/importdata/', methods=['GET', 'POST'])
@login_required
def importdata():
    """ Add data files to database """
    form = ImportDataForm()
    if form.validate_on_submit():
        duplicates = 0
        candidates = glob.glob(f'{form.path.data}/**/*', recursive=True)
        for path in candidates:
            if os.path.isfile(path):
                path = os.path.abspath(path)
                data = fabio.open(path).data
                datahash = hashlib.sha1(data).hexdigest()

                stmt = exists().where(DataFile.hash == datahash)
                duplicate = bool(list(db.session.query(DataFile).filter(stmt)))
                duplicates += duplicate

                if duplicate:
                    continue

                DataFile(datahash, path, session['user_id']).save()

        flash(f'Imported {len(candidates)} files into database for tagging! '
              f'Found {duplicates} duplicates.', 'success')
    else:
        flash_errors(form)
    return render_template('users/importdata.html', form=form)
