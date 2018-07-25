# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, make_response, flash, session, redirect, url_for
from tagcam.utils import flash_errors
from flask_login import login_required
from .forms import TagForm, ImportDataForm, TomoTagForm, ImportTomoDataForm
from tagcam.user.models import Tag, DataFile, TomoTag, TomoDataFile, db
from sqlalchemy.sql import exists
import os
import glob
import fabio
import hashlib
from uuid import uuid4

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

        # reset state
        return redirect(url_for('user.tag'))

    else:
        flash_errors(form)
    return render_template('users/tag.html', form=form)

@blueprint.route('/tomotag/', methods=['GET', 'POST'])
@login_required
def tomotag():
    """Tag an image."""
    form = TomoTagForm()
    print('dir:', dir(form))
    if form.validate_on_submit():

        newtag = TomoTag(hash=form.hash.data,
                     path=form.path.data,
                     username=session["user_id"],
                     **{taglabel: getattr(form, taglabel).data for taglabel in form.tags},
                     )
        newtag.save()

        datafile = db.session.query(DataFile).filter_by(hash=form.hash.data).first()
        datafile.tagged += 1

        db.session.commit()

        # tags = ', '.join([taglabel for taglabel in form.tags if getattr(form, taglabel).data])
        # if tags:
        #     flash(f'Image tagged with {tags}!', 'success')

        # reset state
        return redirect(url_for('user.tomotag'))

    else:
        flash_errors(form)
    return render_template('users/tomotag.html', form=form)


import_blacklist = ['autoexpose_test', 'beamstop_test', '_lo_', '_low_']

def checkblacklist(path):
    for s in import_blacklist:
        if s in path:
            try:
                os.remove(path)
            except OSError:
                pass
            return True


@blueprint.route('/importdata/', methods=['GET', 'POST'])
@login_required
def importdata():
    """ Add data files to database """
    form = ImportDataForm()
    if form.validate_on_submit():
        duplicates = 0
        deleted = 0
        candidates = glob.glob(f'{form.path.data}/**/*', recursive=True)
        for path in candidates:
            if os.path.isfile(path):

                if checkblacklist(path):
                    continue

                path = os.path.abspath(path)

                try:
                    data = fabio.open(path).data
                except OSError:
                    continue

                datahash = hashlib.sha1(data).hexdigest()

                stmt = exists().where(DataFile.hash == datahash)
                duplicate = bool(list(db.session.query(DataFile).filter(stmt)))
                duplicates += duplicate

                if duplicate:
                    continue

                DataFile(datahash, path, session['user_id']).save()

        flash(f'Imported {len(candidates)} files into database for tagging! '
              f'Found {duplicates} duplicates. Deleted {deleted} blacklisted files.', 'success')
    else:
        flash_errors(form)
    return render_template('users/importdata.html', form=form)

# /home/rp/Downloads/20180531_123413_bp-c-40-sprayRingPRwidth0050______00963.tiff
# /home/rp/Downloads/20180531_123413_bp-c-40-spray_00963_Ring Removal_width_0050.tiff

@blueprint.route('/importtomodata/', methods=['GET', 'POST'])
@login_required
def importtomodata():
    """ Add data files to database """
    form = ImportTomoDataForm()
    if form.validate_on_submit():
        duplicates = 0
        deleted = 0
        candidates = glob.glob(f'{form.path.data}/**/*.tif*', recursive=True)
        for path in candidates:
            if os.path.isfile(path):

                # if checkblacklist(path):
                #     continue

                path = os.path.abspath(path)

                try:
                    data = fabio.open(path).data
                except OSError:
                    continue

                datahash = hashlib.sha1(data).hexdigest()

                stmt = exists().where(DataFile.hash == datahash)
                duplicate = bool(list(db.session.query(DataFile).filter(stmt)))
                duplicates += duplicate

                if duplicate:
                    continue

                basename = os.path.splitext(os.path.basename(path))[0]
                frame = basename.split('_')[-1]
                value = basename.split('_')[-2]
                parameter = basename.split('_')[-3]
                operation = basename.split('_')[-4]
                operationtype = basename.split('_')[-5]

                groupid = hashlib.sha1(basename[:-2].encode()).hexdigest()

                TomoDataFile(datahash, path, session['user_id'], groupid=groupid, value=value, parameter=parameter, operation=operation, operationtype=operationtype).save()

        flash(f'Imported {len(candidates)} files into database for tagging! '
              f'Found {duplicates} duplicates. Deleted {deleted} blacklisted files.', 'success')
    else:
        flash_errors(form)
    return render_template('users/importdata.html', form=form)