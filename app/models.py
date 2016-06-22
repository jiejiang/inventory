__author__ = 'jie'
# -*- coding: utf-8 -*-

import uuid, datetime, re, sys
from . import db

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), index=True, unique=True, nullable=False)
    percentage = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    creation_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completion_time = db.Column(db.DateTime, default=None)
    message = db.Column(db.Text)

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
    def new():
        id = str(uuid.uuid4())
        job = Job(uuid=id, percentage=0, status=Job.Status.WAITING)
        db.session.add(job)
        db.session.commit()
        return job

    def delete(self):
        self.status = Job.Status.DELETED
        db.session.commit()


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

    SUFFIXES = set([u"省", u"市", u"县", u"区"])

    def __unicode__(self):
        return self.name

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
                        assert(type == City.Type.COUNTRY)
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
        if name[-1] in City.SUFFIXES:
            return find_routine(name[:-1])
        else:
            for suffix in City.SUFFIXES:
                city = find_routine(name + suffix.decode('utf8'))
                if city:
                    return city
        return None
