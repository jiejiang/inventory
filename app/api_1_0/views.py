# -*- coding: utf-8 -*-
from sqlalchemy import not_

__author__ = 'jie'

import sys

import os, datetime, zipfile
from flask import request, current_app, Response
from flask_restful import Resource, fields, marshal_with
from flask_restful import abort, reqparse
from redis import ConnectionError
from sqlalchemy.orm import exc
import pandas as pd
from . import api
from .. import db
from ..models import Job, Order, Retraction
from ..util import time_to_filename
from ..main.postorder import read_order_numbers, retract_from_order_numbers

STREAM_BUF_SIZE = 2048

def get_object_or_404(model, *criterion):
    try:
        return model.query.filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)

file_download_parser = reqparse.RequestParser()
file_download_parser.add_argument('id', type=str, help="File ID!")

class BatchOrderListAPI(Resource):
    def post(self):
        from ..main.jobs import batch_order

        file = request.files['file']
        if file:
            job = None
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'
                job = Job.new()
                fileid = job.uuid + '.' + ext
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                save_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], fileid)
                file.save(save_filename)

                workdir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job.uuid)
                if not os.path.exists(workdir):
                    os.makedirs(workdir)

                batch_order.delay(job.uuid, save_filename, workdir)

                return {'id': job.uuid, }
            except ConnectionError, inst:
                if job:
                    job.delete()
                abort(500, message="Job system Offline!")
            except Exception, inst:
                if job:
                    job.delete()
                import traceback
                traceback.print_exc(sys.stderr)
                abort(500, message=str(inst))
        else:
            abort(500, message="File not attached!")

    def get(self):
        args = file_download_parser.parse_args()
        filename = os.path.join(current_app.config['DOWNLOAD_FOLDER'], args['id'], args['id'] + '.zip')
        job = get_object_or_404(Job, Job.uuid==args['id'])
        download_filename = u"生成_".encode('utf8') + time_to_filename(job.completion_time) + '.zip'
        if not os.path.exists(filename):
            abort(404, message="File not exist")

        def generate():
            with open(filename, 'rb') as f:
                buf = f.read(STREAM_BUF_SIZE)
                while buf:
                    yield buf
                    buf = f.read(STREAM_BUF_SIZE)

        response = Response(generate(), mimetype='application/octet-stream',
                            headers={"Content-Disposition": "attachment;filename=%s" % download_filename})
        return response


class JobAPI(Resource):
    fields = {'id': fields.String(attribute='uuid'), 'status': fields.String(attribute='status_string'),
                  'creationTime': fields.DateTime(dt_format='iso8601', attribute='creation_time'),
                  'completionTime': fields.DateTime(dt_format='iso8601', attribute='completion_time'),
                  'percentage': fields.String, 'message': fields.String,
                  'finished': fields.Boolean(attribute='finished'), 'success': fields.Boolean(attribute='success'),
                  'order_numbers': fields.Nested({v: fields.List(fields.String) for k, v in Order.Type.types.items()})}

    @marshal_with(fields)
    def get(self, job_id):
        job = get_object_or_404(Job, Job.uuid==job_id)
        return job, 200, {'Last-Modified': datetime.datetime.now(),
                          'Cache-Control': 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0',
                          'Pragma' : 'no-cache', 'Expires': -1}


class OrderListAPI(Resource):
    def post(self):
        file = request.files['file']
        if file:
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'

                df = pd.read_excel(file)

                inserted_order_numbers = {}
                invalid_order_numbers = []
                existing_order_numbers = []
                found = False
                for type_int, type_string in Order.Type.types.items():
                    inserted_order_numbers[type_string] = []
                    if type_string in df.columns:
                        found = True
                        for order_number in df[type_string]:
                            order_number = str(order_number).strip()
                            if order_number:
                                if not Order.is_order_number_valid(type_int, order_number):
                                    invalid_order_numbers.append(order_number)
                                    continue
                                if Order.query.filter_by(order_number=order_number).scalar() is not None:
                                    existing_order_numbers.append(order_number)
                                    continue
                                order = Order(order_number=order_number, type=type_int)
                                db.session.add(order)
                                inserted_order_numbers[type_string].append(order_number)
                db.session.commit()
                if not found:
                    raise Exception, u"输入未包含有效订单列"
                return {'inserted_order_numbers': inserted_order_numbers, 'invalid_order_numbers' : invalid_order_numbers,
                        'existing_order_numbers' : existing_order_numbers}
            except Exception, inst:
                db.session.rollback()
                import traceback
                traceback.print_exc(sys.stderr)
                abort(500, message=str(inst))
        else:
            abort(500, message="File not attached!")

    def get(self):
        stats = {}
        for type_id, type_name in Order.Type.types.items():
            query = Order.query.filter_by(type=type_id)
            stats[type_name] = {
                'unused': query.filter_by(used=False).count(),
                'used': query.filter_by(used=True).count(),
            }
        used_query = Order.query.filter_by(used=True)
        used_count = used_query.count()
        unretracted_count = used_query.filter_by(retraction=None).count()
        return { 'stats' :stats, 'used_count' : used_query.count(), 'unretracted_count': unretracted_count,
                 'retracted_count': used_count - unretracted_count }

class RetractionAPI(Resource):
    def post(self):
        file = request.files['file']
        if file:
            curdir = os.getcwd()
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'

                order_numbers = read_order_numbers(file)
                if len(order_numbers) <= 0:
                    raise Exception, u"输入[提取单号]列为空"

                retraction = Retraction.new()
                outdir = os.path.join(os.path.join(current_app.config['RETRACTION_FOLDER']), retraction.uuid)
                tmpdir = os.path.join(os.path.join(outdir), "tmp")
                if os.path.exists(outdir):
                    raise Exception, u"uuid目录已用:%s" % retraction.uuid
                os.makedirs(outdir)
                retract_from_order_numbers(current_app.config['DOWNLOAD_FOLDER'], order_numbers, tmpdir, retraction)
                outfile = os.path.abspath(os.path.join(outdir, retraction.uuid + ".zip"))
                os.chdir(tmpdir)
                zf = zipfile.ZipFile(outfile, "w", compression=zipfile.ZIP_DEFLATED)
                for root, dirs, files in os.walk("."):
                    if root <> ".":
                        zf.write(root)
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        zf.write(filepath, arcname=filepath.decode('utf8'))
                zf.close()
                retraction.success = True
                db.session.commit()
                return {'order_numbers': order_numbers.tolist(), 'id': retraction.uuid}
            except Exception, inst:
                db.session.rollback()
                import traceback
                traceback.print_exc(sys.stderr)
                abort(500, message=str(inst))
            finally:
                os.chdir(curdir)
        else:
            abort(500, message="File not attached!")

    def get(self):
        args = file_download_parser.parse_args()
        filename = os.path.join(current_app.config['RETRACTION_FOLDER'], args['id'], args['id'] + '.zip')
        retraction = get_object_or_404(Retraction, Retraction.uuid==args['id'])
        download_filename = u"提取_".encode('utf8') + time_to_filename(retraction.timestamp) + '.zip'
        if not os.path.exists(filename):
            abort(404, message="File not exist")

        def generate():
            with open(filename, 'rb') as f:
                buf = f.read(STREAM_BUF_SIZE)
                while buf:
                    yield buf
                    buf = f.read(STREAM_BUF_SIZE)

        response = Response(generate(), mimetype='application/octet-stream',
                            headers={"Content-Disposition": "attachment;filename=%s" % download_filename})
        return response

api.add_resource(BatchOrderListAPI, '/batch-order')
api.add_resource(JobAPI, '/job/<job_id>')
api.add_resource(OrderListAPI, '/orders')
api.add_resource(RetractionAPI, '/retract-orders')