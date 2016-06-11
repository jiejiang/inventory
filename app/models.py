__author__ = 'jie'

import uuid, datetime
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

