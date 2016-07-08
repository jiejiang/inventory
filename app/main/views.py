# -*- coding: utf-8 -*-
__author__ = 'jie'

import os
from flask import redirect, url_for, current_app, abort, Response
from . import main
from ..models import Job, Retraction
from ..util import time_to_filename
from flask_user import login_required

@main.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('front_end.index'))

STREAM_BUF_SIZE = 2048

@main.route("/download-job-file/<job_id>", methods=['GET',])
@login_required
def download_job_file(job_id):
    job = Job.query.filter_by(id=job_id).first()
    if job is None:
        abort(404, "File not exist")
    filepath = os.path.join(current_app.config['DOWNLOAD_FOLDER'], job.uuid, job.uuid+".zip")
    if not os.path.exists(filepath):
        abort(404, "File not exist 2.")

    def generate():
        with open(filepath, 'rb') as f:
            buf = f.read(STREAM_BUF_SIZE)
            while buf:
                yield buf
                buf = f.read(STREAM_BUF_SIZE)
    response = Response(generate(), mimetype='application/octet-stream',
            headers={"Content-Disposition": "attachment;filename=%s" % "%s.zip" %
                                            (u"生成_".encode('utf8') + time_to_filename(job.completion_time))})
    return response

@main.route("/download-retraction-file/<retraction_id>", methods=['GET',])
@login_required
def download_retraction_file(retraction_id):
    retraction = Retraction.query.filter_by(id=retraction_id).first()
    if retraction is None:
        abort(404, "File not exist")
    filepath = os.path.join(current_app.config['RETRACTION_FOLDER'], retraction.uuid, retraction.uuid+".zip")
    if not os.path.exists(filepath):
        abort(404, "File not exist 2.")

    def generate():
        with open(filepath, 'rb') as f:
            buf = f.read(STREAM_BUF_SIZE)
            while buf:
                yield buf
                buf = f.read(STREAM_BUF_SIZE)
    response = Response(generate(), mimetype='application/octet-stream',
            headers={"Content-Disposition": "attachment;filename=%s" % "%s.zip" %
                                            (u"提取_".encode('utf8') + time_to_filename(retraction.timestamp))})

    return response
