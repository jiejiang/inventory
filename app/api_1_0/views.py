__author__ = 'jie'

import sys

import os
from flask import request, current_app, Response
from flask_restful import Resource, fields, marshal_with
from flask_restful import abort, reqparse
from redis import ConnectionError
from sqlalchemy.orm import exc
import pandas as pd
from . import api
from .. import db
from ..models import Job, Order

STREAM_BUF_SIZE = 2048

def get_object_or_404(model, *criterion):
    try:
        return model.query.filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)

file_download_parser = reqparse.RequestParser()
file_download_parser.add_argument('id', type=str, help="Job ID!")
file_download_parser.add_argument('filename', type=str, help="File Name!")

class BatchOrderListAPI(Resource):
    def post(self):
        from ..main.jobs import batch_order

        file = request.files['file']
        if file:
            job = None
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt":
                    raise Exception, 'Only .xlt file is supported!'
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
        download_filename = args['filename'] + '.zip'
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
        return job


class OrderListAPI(Resource):
    def post(self):
        file = request.files['file']
        if file:
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlsx":
                    raise Exception, 'Only .xlt file is supported!'

                df = pd.read_excel(file)

                inserted_order_numbers = {}
                invalid_order_numbers = []
                existing_order_numbers = []
                for type_int, type_string in Order.Type.types.items():
                    inserted_order_numbers[type_string] = []
                    if type_string in df.columns:
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
        used_count = Order.query.filter_by(used=True).count()
        return { 'stats' :stats, 'used_count' : used_count }

api.add_resource(BatchOrderListAPI, '/batch-order')
api.add_resource(JobAPI, '/job/<job_id>')
api.add_resource(OrderListAPI, '/orders')
