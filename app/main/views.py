__author__ = 'jie'

import os
from flask import redirect, url_for, current_app, abort, Response
from . import main
from ..models import Job

@main.route("/", methods=['GET', 'POST'])
def index():
    return redirect(url_for('front_end.index'))

STREAM_BUF_SIZE = 2048

@main.route("/download-job-file/<job_id>", methods=['GET',])
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
            headers={"Content-Disposition": "attachment;filename=%s" % "archive-%s.zip" % job.uuid})

    return response