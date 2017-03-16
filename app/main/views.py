# -*- coding: utf-8 -*-
__author__ = 'jie'

import os, datetime
import pandas as pd
from cStringIO import StringIO
from werkzeug.utils import secure_filename
from flask import redirect, url_for, current_app, abort, Response, send_from_directory, request
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

@main.route("/tts/<sentence>", methods=['GET',])
@login_required
def tts(sentence):
    filename = secure_filename(sentence) + '.wav'
    tts_folder = current_app.config["TTS_FOLDER"]
    filepath = os.path.join(tts_folder, filename)
    if not os.path.exists(tts_folder):
        os.makedirs(tts_folder)
    if not os.path.exists(filepath):
        os.system("""pico2wave -w "%s" -l en-GB "%s" """ % (filepath, sentence))
    if not os.path.exists(filepath):
        abort(500, message="Failed to TTS")
    return send_from_directory(os.path.abspath(tts_folder), filename, as_attachment=True, mimetype='application/octet-stream')


@main.route("/scan-export", methods=['POST',])
@login_required
def scan_export():
    if not 'barcodes' in request.form:
        abort(500)
    barcodes = request.form['barcodes'].split(",")
    df = pd.DataFrame({u"提取单号": barcodes})
    xlsx_file = StringIO()
    writer = pd.ExcelWriter(xlsx_file, engine='xlsxwriter')
    df.to_excel(writer, index=None)
    writer.save()
    xlsx_file.seek(0)
    return Response(xlsx_file, mimetype='application/octet-stream',
            headers={"Content-Disposition": "attachment;filename=%s" %
                                            "scan_%s.xlsx" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")})
