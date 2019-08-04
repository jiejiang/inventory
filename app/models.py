# -*- coding: utf-8 -*-
__author__ = 'jie'

import uuid, datetime, re, sys
from sqlalchemy import desc, asc, Index, UniqueConstraint, and_
from flask_user import UserMixin
from . import db

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), index=True, unique=True, nullable=False)
    percentage = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    creation_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completion_time = db.Column(db.DateTime, default=None)
    message = db.Column(db.Text)
    orders = db.relationship("Order", backref='job', lazy='dynamic')
    version = db.Column(db.String(16), nullable=True, default="")
    issuer = db.Column(db.String(128), index=True, nullable=True)

    class Status:
        WAITING = 0
        PROCESSING = 1
        COMPLETED = 2
        FAILED = 4
        DELETED = 8

        status_names = {
            WAITING: "Waiting",
            PROCESSING: "Processing",
            COMPLETED: "Completed",
            FAILED: "Failed",
            DELETED: "Deleted",
        }

    @property
    def status_string(self):
        if self.status in Job.Status.status_names:
            return Job.Status.status_names[self.status]
        else:
            raise Exception, "Invalid status code"

    @property
    def finished(self):
        return self.status <> Job.Status.WAITING and self.status <> Job.Status.PROCESSING

    @property
    def success(self):
        return self.status == Job.Status.COMPLETED

    @staticmethod
    def new(issuer=None):
        id = str(uuid.uuid4())
        job = Job(uuid=id, percentage=0, status=Job.Status.WAITING, issuer=issuer)
        db.session.add(job)
        db.session.commit()
        return job

    def delete(self):
        self.status = Job.Status.DELETED
        db.session.commit()

    @property
    def order_numbers(self):
        order_numbers = {}
        for type_id, type_name in Order.Type.types.items():
            order_numbers[type_name] = [order.order_number for order in Order.query.filter_by(type=type_id, job_id=self.id).all()]
        return order_numbers

class City(db.Model):
    __tablename__ = "city"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=True)
    name = db.Column(db.String(32), nullable=False, index=True)
    type = db.Column(db.Integer, nullable=False, index=True)

    class Type:
        NATION = 0
        PROVINCE = 1
        MUNICIPALITY = 2
        COUNTY = 3

        types = {
            NATION : "Nation",
            PROVINCE : "Province",
            MUNICIPALITY : "Municipality",
            COUNTY : "County",
        }

    SUFFIXES = [u"省", u"市", u"县", u"区"]
    SUFFIXES_SET = set(SUFFIXES)

    ADD_SUFFIXES = [u"省", u"市", u"盟"]
    DEL_SUFFIXES_SET = set(SUFFIXES)

    def __unicode__(self):
        return "%s[%d]" % (self.name, self.type)

    DISTRICTS = [u'北京', u'上海', u'重庆', u'天津']
    DISTRICTS_FULLNAME = [x + u"市" for x in DISTRICTS]
    AUTONOMOUS_SPECIAL_REGION = {
        u'新疆' : u'新疆维吾尔自治区',
        u'广西' : u'广西壮族自治区',
        u'宁夏' : u'宁夏回族自治区',
        u'内蒙古' : u'内蒙古自治区',
        u'西藏' : u'西藏自治区',
        u'香港' : u'香港特别行政区',
        u'澳门' : u'澳门特别行政区'
    }
    AUTONOMOUS_SPECIAL_REGION_REVERSE = {v: k for k, v in AUTONOMOUS_SPECIAL_REGION.iteritems()}
    MUNICIPAL_SUFFIX_SET = set([u"市", u"县", u"区", u"盟"])

    @staticmethod
    def normalize_province(name):
        if name in City.DISTRICTS:
            return name + u"市"
        elif name in City.AUTONOMOUS_SPECIAL_REGION:
            return City.AUTONOMOUS_SPECIAL_REGION[name]
        else:
            return name + u"省"

    @staticmethod
    def denormalize_province(name):
        if name in City.DISTRICTS_FULLNAME:
            return name[:-1]
        elif name in City.AUTONOMOUS_SPECIAL_REGION_REVERSE:
            return City.AUTONOMOUS_SPECIAL_REGION_REVERSE[name]
        if name.endswith(u"省"):
            return name[:-1]

    @staticmethod
    def normalize_municipality(name):
        return name + u"市" if not name[-1] in City.MUNICIPAL_SUFFIX_SET else name

    @staticmethod
    def denormalize_municipality(name):
        return name[:-1] if name and name[-1] in City.MUNICIPAL_SUFFIX_SET else name

    @staticmethod
    def normalize_province_path(cities):
        if not cities or len(cities) > 3:
            raise Exception, "Empty or too long province info"
        for i, type in enumerate((City.Type.PROVINCE, City.Type.MUNICIPALITY, City.Type.COUNTY)):
            if i >= len(cities):
                break
            assert(cities[i].type == type)
        province_name = City.normalize_province(cities[0].name)
        municipal_name = City.normalize_municipality(cities[1].name) \
            if len(cities) > 1 and cities[0].name <> cities[1].name else ""

        if len(cities) < 3:
            return province_name, municipal_name, ""
        else:
            if cities[2].name.endswith(u'市'):         #check if 地级市
                return province_name, cities[2].name, ""
            else:
                return province_name, municipal_name, cities[2].name

    @staticmethod
    def populate(filename):
        cities = {}
        insert_re = re.compile(r"^\s*INSERT\s+INTO\s+.*?\((\d+),(\d+),'(.*?)',(\d+)\);\s*$")
        with open(filename) as f:
            for line in f:
                m = insert_re.match(line)
                if m:
                    id = int(m.group(1))
                    parent_id = int(m.group(2))
                    name = m.group(3).decode('utf-8')
                    type = int(m.group(4))
                    if not type in City.Type.types:
                        raise Exception, "Cannot find type: %s" % line
                    if parent_id <> 0 and not parent_id in cities:
                        raise Exception, "Cannot find parent: %s" % line
                    if id in cities:
                        raise Exception, "Duplicated city: %s" % line
                    if parent_id <> 0:
                        parent = cities[parent_id]
                        city = City(name = name, parent_id=parent.id, type=type)
                    else:
                        assert(type == City.Type.NATION)
                        city = City(name = name, type=type)
                    db.session.add(city)
                    db.session.commit()
                    cities[id] = city
                    print >> sys.stderr, city.id
                else:
                    print >> sys.stderr, "ignore: %s" % line

    @staticmethod
    def find_province(name):
        name = name.strip()
        if name == "":
            return None

        def find_routine(name):
            cities = City.query.filter_by(name=name).order_by(City.type).all()
            for city in cities:
                if city.type == City.Type.PROVINCE:
                    return city
            for city in cities:
                while city:
                    if city.type == City.Type.PROVINCE:
                        return city
                    elif city.type == City.Type.MUNICIPALITY or city.type == City.Type.COUNTY:
                        parent = City.query.filter_by(id=city.parent_id).first()
                        if not parent:
                            raise Exception, "Cannot find valid parent: %s" % city.name
                        city = parent
                raise Exception, "Failed to find with child"
            return None

        city = find_routine(name)
        if city:
            return city
        if name[-1] in City.SUFFIXES_SET:
            return find_routine(name[:-1])
        else:
            for suffix in City.SUFFIXES:
                city = find_routine(name + suffix.decode('utf8'))
                if city:
                    return city
        return None


    @staticmethod
    def find_province_path(name):
        name = name.strip()
        if name == "":
            return None

        def find_routine(name):
            cities = City.query.filter_by(name=name).order_by(City.type).all()
            for city in cities:
                if city.type == City.Type.PROVINCE:
                    return [city,]
            for city in cities:
                res = []
                while city:
                    if city.type == City.Type.PROVINCE:
                        res.append(city)
                        res.reverse()
                        return res
                    elif city.type == City.Type.MUNICIPALITY or city.type == City.Type.COUNTY:
                        res.append(city)
                        parent = City.query.filter_by(id=city.parent_id).first()
                        if not parent:
                            raise Exception, "Cannot find valid parent: %s" % city.name
                        city = parent
                raise Exception, "Failed to find with child"
            return None

        city = find_routine(name)
        if city:
            return city
        if name[-1] in City.DEL_SUFFIXES_SET:
            return find_routine(name[:-1])
        else:
            for suffix in City.ADD_SUFFIXES:
                new_name = name + suffix.decode('utf8')
                if new_name <> u"西盟":
                    city = find_routine(new_name)
                if city:
                    return city
        return None


class Order(db.Model):
    __tablename__ = "order"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(128), unique=True, nullable=False, index=True)
    type = db.Column(db.Integer, index=True, default=1)
    upload_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    used = db.Column(db.Boolean, index=True, nullable=False, default=False)
    used_time = db.Column(db.DateTime)
    sender_address = db.Column(db.String(256))
    receiver_address = db.Column(db.String(256))
    receiver_name = db.Column(db.String(32))
    receiver_id_number = db.Column(db.String(64))
    receiver_mobile = db.Column(db.String(64))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    retraction_id = db.Column(db.Integer, db.ForeignKey('retraction.id'), nullable=True)
    discarded_time = db.Column(db.DateTime, nullable=True, default=None)

    class Type:
        CNPOST = 1
        BEUK = 2
        YUANTONG = 3

        DEFAULT_TYPE = CNPOST

        types = {
            CNPOST : u"邮政单号",
            BEUK : u'BEUK单号',
            YUANTONG : u'圆通单号',
        }

        route2type = {
            'cnpost': CNPOST,
            'beuk': BEUK,
            'yuantong': YUANTONG,
        }

        @classmethod
        def route_as_type(cls, route):
            return cls.route2type.get(route, None)

    def discard(self):
        if self.retraction_id:
            raise Exception, "Cannot discard extracted order"
        self.discarded_time = datetime.datetime.now()

    def make_reusable(self):
        raise Exception, "Not allowed"
        self.used = False
        self.used_time = None
        self.sender_address = None
        self.receiver_address = None
        self.receiver_name = None
        self.receiver_id_number = None
        self.receiver_mobile = None
        self.job_id = None
        self.retraction_id = None

    @property
    def type_name(self):
        if self.type in Order.Type.types:
            return Order.Type.types[self.type]
        else:
            raise Exception, "Invalid order type: %d" % self.type

    @staticmethod
    def is_order_number_valid(type, order_number):
        return (type == Order.Type.CNPOST and re.match(r"^\d+$", order_number)) or \
               (type == Order.Type.BEUK and re.match(r"^[a-zA-Z]+$", order_number))

    @staticmethod
    def pick_first(type):
        if not type in Order.Type.types:
            raise Exception, "Invalid type to choose from: %s" % type
        return Order.query.filter_by(type=type, used=False, discarded_time=None).order_by(asc(Order.id)).first()

    @staticmethod
    def pick_unused():
        return Order.query.filter_by(used=False, discarded_time=None).order_by(asc(Order.id)).first()

    @staticmethod
    def find_by_order_number(order_number):
        return Order.query.filter_by(order_number=str(order_number)).first()


class Retraction(db.Model):
    __tablename__ = "retraction"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), index=True, unique=True, nullable=False)
    success = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    message = db.Column(db.Text)
    orders = db.relationship("Order", backref='retraction', lazy='dynamic')

    is_redo = db.Column(db.Boolean, default=False)

    @staticmethod
    def new():
        id = str(uuid.uuid4())
        retraction = Retraction(uuid=id)
        return retraction

    def __unicode__(self):
        return self.uuid


product_routes = db.Table('product_routes',
    db.Column('route_id', db.Integer, db.ForeignKey('route.id'), primary_key=True),
    db.Column('product_info_id', db.Integer, db.ForeignKey('product_info.id'), primary_key=True)
)


class Route(db.Model):
    __tablename__ = "route"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), nullable=False, index=True, unique=True)
    name = db.Column(db.String(128), nullable=False)
    products = db.relationship('ProductInfo', secondary=product_routes, lazy='subquery',
                           backref=db.backref('routes', lazy=True))

    def __str__(self):
        return self.name


class ProductInfo(db.Model):
    __tablename__ = "product_info"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True, unique=True)
    net_weight = db.Column(db.Float, nullable=False)
    full_name = db.Column(db.String(128), nullable=False, unique=True, index=True)
    deprecated = db.Column(db.Boolean, default=False)
    count_infos = db.relationship("ProductCountInfo", backref='product_info', lazy='dynamic')

    dutiable_as_any_4_pieces = db.Column(db.Boolean, default=False)
    non_dutiable_as_all_6_pieces = db.Column(db.Boolean, default=False)

    # new attribute
    unit_price = db.Column(db.Float)
    gross_weight = db.Column(db.Float)
    tax_code = db.Column(db.String(64))
    billing_unit = db.Column(db.String(32))
    billing_unit_code = db.Column(db.String(32))
    unit_per_item = db.Column(db.Float)
    specification = db.Column(db.String(64))

    # bc attribute
    bc_product_code = db.Column(db.String(64))
    bc_specification = db.Column(db.String(64))
    bc_second_quantity = db.Column(db.String(64))
    bc_measurement_unit = db.Column(db.String(64))
    bc_second_measurement_unit = db.Column(db.String(64))

    # new name
    report_name = db.Column(db.String(128))

    # tickets
    ticket_name = db.Column(db.String(128))
    ticket_price = db.Column(db.Float)

    waybill_name = db.Column(db.String(128))

    #deprecated
    price_per_kg = db.Column(db.Float)

    def __str__(self):
        return self.full_name

    @property
    def count_info_string(self):
        """deprecated"""
        return "<br/>".join(sorted([u"%s件 -- %g KG" % (count_info.count, count_info.gross_weight_per_box)
                                  for count_info in self.count_infos]))

    @staticmethod
    def find_product_and_weight(item_name, item_count):
        """deprecated"""
        return ProductInfo.query.filter(and_(ProductInfo.name==item_name, ProductInfo.deprecated==False))\
            .join(ProductCountInfo, ProductCountInfo.product_info_id==ProductInfo.id)\
            .add_column(ProductCountInfo.gross_weight_per_box)\
            .filter(ProductCountInfo.count==item_count).first()

class ProductCountInfo(db.Model):
    __tablename__ = "product_count_info"
    id = db.Column(db.Integer, primary_key=True)
    product_info_id = db.Column(db.Integer, db.ForeignKey('product_info.id'), nullable=True, index=True)
    count = db.Column(db.Integer, nullable=False, index=True)
    gross_weight_per_box = db.Column(db.Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_info_id", "count"),
    )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User Authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, default='')
    reset_password_token = db.Column(db.String(100), nullable=False, default='')

    # User Email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    is_enabled = db.Column(db.Boolean(), nullable=False, default=False)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')

    def is_active(self):
        return self.is_enabled

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%s -- %s" % (self.username, self.email)

    @staticmethod
    def create_new(user_manager, username, email, password):
        u = User(username=username, email=email, password=user_manager.hash_password(password),
                 confirmed_at=datetime.datetime.utcnow(), is_enabled=True)
        db.session.add(u)
        db.session.commit()



