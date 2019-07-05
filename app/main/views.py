# -*- coding: utf-8 -*-
__author__ = 'jie'

import os, datetime, sys
import pandas as pd
from cStringIO import StringIO
from werkzeug.utils import secure_filename
from flask import redirect, url_for, current_app, abort, Response, send_from_directory, request, flash
from . import main
from ..models import Job, Retraction
from ..util import time_to_filename
from flask_user import login_required
from openpyxl import load_workbook
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows

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

@main.route("/merge-excel", methods=['POST'])
@login_required
def merge_excel():
    try:
        if not request.files or len(request.files.getlist('files')) < 2:
            raise Exception, u"无文件或文件个数不够"
        files = request.files.getlist('files')
        first_df = pd.read_excel(files[0])
        columns = first_df.columns
        other_dfs = map(lambda x: pd.read_excel(x, converters={
            key: lambda x: str(x) for key in columns
        }), files[1:], )
        data_df = pd.DataFrame()
        for _df in other_dfs:
            if not _df.columns.equals(columns):
                raise Exception, u"Excel格式不同"
            data_df = data_df.append(_df, ignore_index=True)
        #TODO add or modify sequential information in combined
        files[0].seek(0)
        wb = load_workbook(filename=BytesIO(files[0].read()))
        ws = wb["Sheet1"]
        for r in dataframe_to_rows(data_df, index=False, header=False):
            ws.append(r)
        xlsx_file = StringIO()
        wb.save(xlsx_file)
        xlsx_file.seek(0)
        return Response(xlsx_file, mimetype='application/octet-stream',
                        headers={"Content-Disposition": "attachment;filename=%s" %
                                                        (u"合并提取_%s.xlsx" % datetime.datetime.now().strftime(
                            "%Y-%m-%d_%H-%M-%S")).encode('utf-8')})
    except Exception, inst:
        import traceback
        traceback.print_exc(sys.stderr)
        flash(inst.message)
        return redirect(url_for('front_end.index') + '#/merge-excel')
