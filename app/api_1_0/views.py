# -*- coding: utf-8 -*-
import json

__author__ = 'jie'

import sys, json
from sqlalchemy import not_
from werkzeug.utils import secure_filename
import os, datetime, zipfile
from flask import request, current_app, Response, send_from_directory, make_response
from flask_restful import Resource, fields, marshal_with, marshal
from flask_restful import abort, reqparse
from redis import ConnectionError
from sqlalchemy.orm import exc
from sqlalchemy import func, desc, or_, and_
import pandas as pd
from . import api
from .. import db
from ..models import Job, Order, Retraction, City, ProductInfo, Route
from ..util import time_to_filename
from ..main.postorder import read_order_numbers, retract_from_order_numbers, load_order_info, is_dutiable
from auth import http_basic_auth, login_required

STREAM_BUF_SIZE = 2048

def wrap_json_response(data):
    return data, 200, {
        'Last-Modified': datetime.datetime.now(),
        'Cache-Control': 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0',
        'Pragma': 'no-cache', 'Expires': -1}

def get_object_or_404(model, *criterion):
    try:
        return model.query.filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)

file_download_parser = reqparse.RequestParser()
file_download_parser.add_argument('id', type=str, help="File ID!")

class BatchOrderListAPI(Resource):
    method_decorators = [login_required, ]

    def post(self):
        from ..main.jobs import batch_order

        issuer = request.form['issuer'] if 'issuer' in request.form else None
        test_mode = request.form['test_mode'] if 'test_mode' in request.form else False
        route = request.form['route'] if 'route' in request.form else None
        if route:
            order_type = Order.Type.route_as_type(route)
            if not order_type:
                abort(500, message=u'route 无效%d' % route)
        else:
            order_type = Order.Type.DEFAULT_TYPE

        external_order_no = request.form['external_order_no'] if 'external_order_no' in request.form else None

        file = request.files['file']
        if file:
            job = None
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'
                job = Job.new(issuer)
                fileid = job.uuid + '.' + ext
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                save_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], fileid)
                file.save(save_filename)

                workdir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job.uuid)
                if not os.path.exists(workdir):
                    os.makedirs(workdir)

                batch_order.delay(job.uuid, save_filename, workdir, order_type, test_mode=test_mode,
                                  external_order_no=external_order_no)

                return wrap_json_response({'id': job.uuid, })
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
    method_decorators = [login_required, ]

    fields = {'id': fields.String(attribute='uuid'), 'status': fields.String(attribute='status_string'),
                  'creationTime': fields.DateTime(dt_format='iso8601', attribute='creation_time'),
                  'completionTime': fields.DateTime(dt_format='iso8601', attribute='completion_time'),
                  'percentage': fields.String, 'message': fields.String,
                  'finished': fields.Boolean(attribute='finished'), 'success': fields.Boolean(attribute='success'),
                  'order_numbers': fields.Nested({v: fields.List(fields.String) for k, v in Order.Type.types.items()})}

    @marshal_with(fields)
    def get(self, job_id):
        job = get_object_or_404(Job, Job.uuid==job_id)
        return wrap_json_response(job)

class OrderListAPI(Resource):
    method_decorators = [login_required, ]

    def post(self):
        file = request.files['file']
        if file:
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'

                converters = {}
                for type_int, type_string in Order.Type.types.items():
                    converters[type_string] = lambda x:str(x)
                df = pd.read_excel(file, converters=converters)

                inserted_order_numbers = {}
                invalid_order_numbers = []
                existing_order_numbers = []
                found = False
                for type_int, type_string in Order.Type.types.items():
                    inserted_order_numbers[type_string] = []
                    if type_string in df.columns:
                        found = True
                        for order_number in df[~df[type_string].isnull()][type_string]:
                            print order_number
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
                return wrap_json_response({'inserted_order_numbers': inserted_order_numbers, 'invalid_order_numbers' : invalid_order_numbers,
                        'existing_order_numbers' : existing_order_numbers})
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
        return wrap_json_response({ 'stats' :stats, 'used_count' : used_query.count(), 'unretracted_count': unretracted_count,
                 'retracted_count': used_count - unretracted_count,
                 'alert_thresholds' : current_app.config['ALERT_THRESHOLDS']})

class RetractionAPI(Resource):
    method_decorators = [login_required, ]

    def post(self):
        if not 'route' in request.form:
            abort(500, message=u"无线路选择")
        route = request.form['route']
        if not route in current_app.config['ROUTE_CONFIG']:
            abort(500, message=u"线路选择错误")
        route_config = current_app.config['ROUTE_CONFIG'][route]
        dryrun = request.form.get('dryrun', False)
        file = request.files['file']
        is_redo = request.form.get('is_redo', "false") == "true"
        if file:
            curdir = os.getcwd()
            try:
                ext = file.filename.split('.')[-1].lower()
                if ext <> "xlt" and ext <> "xlsx" and ext <> "xls":
                    raise Exception, 'Only .xlt, .xlsx or .xls file is supported!'

                order_numbers = read_order_numbers(file)
                if len(order_numbers) <= 0:
                    raise Exception, u"输入[提取单号]列为空"

                if dryrun:
                    retraction = None
                    outdir = None
                    tmpdir = None
                else:
                    retraction = Retraction.new()
                    retraction.is_redo = is_redo
                    db.session.add(retraction)

                    outdir = os.path.join(os.path.join(current_app.config['RETRACTION_FOLDER']), retraction.uuid)
                    tmpdir = os.path.join(os.path.join(outdir), "tmp")
                    if os.path.exists(outdir):
                        raise Exception, u"uuid目录已用:%s" % retraction.uuid
                    os.makedirs(outdir)

                package_df = retract_from_order_numbers(current_app.config['DOWNLOAD_FOLDER'], order_numbers, tmpdir, route_config,
                                           retraction)
                if dryrun:
                    def join_func(row):
                        receiver = row[u'收件人'].unique()
                        assert (len(receiver) == 1)
                        id_number = row[u'备注'].unique()
                        assert (len(id_number) == 1)
                        dutiable, is_dutiable_category = is_dutiable(row, u'内件名称', row[u"数量"].sum())
                        return pd.Series({
                            'message': '%s Pieces, OK' % row[u"数量"].sum(), 'receiver_name': receiver[0],
                            'receiver_id_number': id_number[0], 'pieces': row[u"数量"].sum(),
                            'dutiable': dutiable,
                            'is_dutiable_category': True if is_dutiable_category else False,
                            'detail': "/".join(map(lambda x: "%s(%s)" % (x[0], x[1]), zip(row[u"内件名称"], row[u"数量"]))),
                        })

                    product_info_df = pd.read_sql_query(ProductInfo.query.filter(ProductInfo.full_name.in_(
                        tuple(set(package_df[u'内件名称'].map(lambda x: str(x)).tolist())))).statement, db.session.bind)
                    product_info_df.rename(columns={'full_name': u'内件名称'}, inplace=True)
                    package_df = pd.merge(package_df, product_info_df, on=u'内件名称')

                    extract_df = package_df[[u'快件单号', u'数量', u'内件名称', u'收件人', u'备注',
                                             'dutiable_as_any_4_pieces', 'non_dutiable_as_all_6_pieces']]\
                        .groupby(u'快件单号').apply(join_func)
                    extract_df['barcode'] = extract_df.index

                    return wrap_json_response(json.loads(extract_df.to_json(orient='records')))
                else:
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
                    return wrap_json_response({'order_numbers': order_numbers.tolist(), 'id': retraction.uuid})
            except Exception, inst:
                if not dryrun:
                    db.session.rollback()
                import traceback
                traceback.print_exc(sys.stderr)
                abort(500, message=str(inst))
            finally:
                if not dryrun:
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


query_order_parser = reqparse.RequestParser()
query_order_parser.add_argument('id', type=str, help="Receiver ID Number", required=False, action='append')
query_order_parser.add_argument('name_mobile', type=str, help="Receiver Name and Mobile, seperated by pipe", required=False, action='append')
query_order_parser.add_argument('days', type=int, help="Number of Days", required=True)

class OrderAPI(Resource):

    fields = {'orderNumber': fields.String(attribute='order_number'),
              'usedTime': fields.DateTime(dt_format='iso8601', attribute='used_time'),
              'receiverName': fields.String(attribute='receiver_name')}

    @marshal_with(fields)
    def get(self):
        http_basic_auth(request.authorization)
        args = query_order_parser.parse_args()
        or_filters = []
        if args['name_mobile']:
            for name_mobile in args['name_mobile']:
                parts = name_mobile.split('|')
                if len(parts) <> 2:
                    abort(500, message="Invalid name_mobile format")
                name, mobile = parts
                or_filters.append(and_(Order.receiver_name==name, Order.receiver_mobile==mobile))
        if args['id']:
            for id in args['id']:
                or_filters.append(func.lower(Order.receiver_id_number) == func.lower(id))
        if not or_filters:
            abort(500, message="Invalid arguments")
        today = datetime.datetime.today()
        start_day = today - datetime.timedelta(days=args['days']+1)
        return wrap_json_response(Order.query.filter(or_(*or_filters))
                                  .filter(Order.used_time >= start_day, Order.discarded_time==None)
                                  .order_by(desc(Order.used_time)).all())

api.add_resource(OrderAPI, '/order')

class RouteInfoAPI(Resource):
    method_decorators = [login_required, ]

    fields = {
        'name': fields.String,
        'max_order_number_per_receiver': fields.String(),
        }

    @marshal_with(fields)
    def get(self, route):
        if not route in current_app.config['ROUTE_CONFIG']:
            abort(500, message="Route Not Exist")
        return wrap_json_response(current_app.config['ROUTE_CONFIG'][route])


api.add_resource(RouteInfoAPI, '/route-info/<route>')

order_info_parser = reqparse.RequestParser()
order_info_parser.add_argument('route', type=str, help="Route", required=True)

class OrderInfoAPI(Resource):
    method_decorators = [login_required, ]

    def get(self, order_number):
        info = {}
        try:
            args = order_info_parser.parse_args()
            route = args['route']
            if not route in current_app.config['ROUTE_CONFIG']:
                raise Exception, "Error: Route"
            route_config = current_app.config['ROUTE_CONFIG'][route]
            order = Order.query.filter(Order.order_number==order_number).first()
            if not order:
                raise Exception, "Error: Barcode Not Found"
            if not order.job_id:
                raise Exception, "Error: Barcode Not Used"
            if order.retraction_id:
                raise Exception, "Error: Barcode Already Scanned"
            if order.discarded_time:
                raise Exception, "Error: Barcode Already Discarded"
            order_df, pieces, dutiable, is_dutiable_category = load_order_info(current_app.config['DOWNLOAD_FOLDER'], order, route_config)
            info['detail'] = "/".join(
                map(lambda x:"%s(%s)" % (x[0], x[1]),
                    zip(order_df[u"内件名称"].map(lambda x:str(x)).tolist(),
                        order_df[u"数量"].map(lambda x:str(x)).tolist())))
            info['message'] = "%d Pieces, OK" % pieces
            info['pieces'] = pieces
            info['dutiable'] = dutiable
            info['is_dutiable_category'] = True if is_dutiable_category else False
            info['receiver_name'] = order.receiver_name
            info['receiver_id_number'] = order.receiver_id_number
            info['success'] = True
        except Exception, inst:
            info['success'] = False
            info['message'] = inst.message
        return wrap_json_response(info)

api.add_resource(OrderInfoAPI, '/scan-order/<order_number>')


class OrderStatusAPI(Resource):
    fields = {
        'orderNumber': fields.String(attribute='order_number'),
        'usedTime': fields.DateTime(dt_format='iso8601', attribute='used_time'),
        'retractionTime': fields.DateTime(dt_format='iso8601', attribute='retraction.timestamp')
    }

    @marshal_with(fields)
    def get(self, order_number):
        http_basic_auth(request.authorization)
        order = Order.query.filter_by(order_number=order_number).first()
        if order and order.used:
            return wrap_json_response(order)
        else:
            abort(404)

api.add_resource(OrderStatusAPI, '/order/<order_number>')


class CityListAPI(Resource):
    method_decorators = [login_required, ]

    filter_city_set = set([
        u"高新开发区",  u"矿区",  u"海州区",  u"桥西区",  u"开发区",  u"宝山区",  u"新市区",  u"高新区",  u"经济技术开发区",
        u"东山区",  u"桥东区",  u"新华区",  u"铁东区",  u"西安区",  u"普陀区",  u"新区",  u"城中区",  u"城关区",  u"河东区",
        u"西湖区",  u"市区",  u"经济开发区",  u"西市区",  u"白云区",  u"清河区",  u"市郊",  u"铁西区",  u"城区",  u"新城区",
        u"朝阳区",  u"太平区",  u"南山区",  u"长安区",  u"江北区",  u"青山区",  u"海原县",  u"中宁县",  u"海南",  u"鼓楼区",
        u"东城区",  u"市中区",  u"向阳区",  u"双桥区",  u"和平区", u"郊区"])

    def get(self):
        names = set()
        def check_dup(name, name2=None):
            if name <> name2 and name in names:
                print "duplicate: %s" % name
            names.add(name)

        provinces = []
        province_set = set()
        for province in City.query.filter_by(type=City.Type.PROVINCE).order_by('id'):
            if province.name in province_set or province.name in CityListAPI.filter_city_set:
                continue
            province_set.add(province.name)

            check_dup(province.name)

            municipals = []
            municipal_set = set()
            for municipal in City.query.filter_by(parent_id=province.id, type=City.Type.MUNICIPALITY).order_by('id'):
                if municipal.name in municipal_set or municipal.name in CityListAPI.filter_city_set:
                    continue
                municipal_set.add(municipal.name)

                check_dup(municipal.name, province.name)

                counties = []
                county_set = set()
                for county in City.query.filter_by(parent_id=municipal.id, type=City.Type.COUNTY).order_by('id'):
                    if county.name in county_set or county.name in CityListAPI.filter_city_set:
                        continue
                    county_set.add(county.name)

                    check_dup(county.name, municipal.name)
                    counties.append({'name' : county.name})
                municipals.append({'name' : municipal.name, 'contains': counties})
            provinces.append({'name' : province.name, 'contains': municipals})
        return make_response(
            json.dumps(provinces, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf8'))

api.add_resource(CityListAPI, '/cities')

product_list_parser = reqparse.RequestParser()
product_list_parser.add_argument('route_code', type=str, help="Route code", required=False)

class ProductListAPI(Resource):
    method_decorators = [login_required, ]

    product_fields = {
        'name': fields.String(),
        'full_name': fields.String(),
    }

    def get(self):
        args = product_list_parser.parse_args()
        route_code = args.get('route_code', None)
        products = ProductInfo.query.filter(ProductInfo.deprecated==False)
        if route_code:
            products = products.filter(ProductInfo.routes.any(Route.code==route_code))
        return wrap_json_response({'products': marshal(products.order_by(ProductInfo.full_name).all(),
                                                       self.product_fields)})

api.add_resource(ProductListAPI, '/products')
