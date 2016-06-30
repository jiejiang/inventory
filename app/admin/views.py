# -*- coding: utf-8 -*-
__author__ = 'jie'

from flask_admin.contrib import sqla
from flask_admin.menu import MenuLink
from sqlalchemy import func, desc, or_

from .. import db
from . import admin
from ..models import Order, Job
from ..util import time_format

class JobAdmin(sqla.ModelView):
    can_delete = False
    can_edit = False
    can_create = False

    def _show_status(view, context, model, name):
        return model.status_string

    column_formatters = {
        'status': _show_status,
        'creation_time': lambda v, c, m, p: time_format(m.creation_time),
        'completion_time': lambda v, c, m, p: time_format(m.completion_time),
    }

class SuccessJobAdmin(JobAdmin):
    list_template = "admin/job/list.html"
    column_searchable_list = ('uuid', 'creation_time')
    column_exclude_list = ('percentage', 'message')
    column_default_sort = ('completion_time', True)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.status == Job.Status.COMPLETED)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.status == Job.Status.COMPLETED)

class FailedJobAdmin(JobAdmin):
    def get_query(self):
        return self.session.query(self.model).filter(or_(self.model.status == Job.Status.FAILED, self.model.status == Job.Status.DELETED))

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(or_(self.model.status == Job.Status.FAILED, self.model.status == Job.Status.DELETED))

class OrderAdmin(sqla.ModelView):
    def _show_type(view, context, model, name):
        return model.type_name

    column_formatters = {
        'type': _show_type,
        'upload_time': lambda v, c, m, p: time_format(m.upload_time),
        'used_time': lambda v, c, m, p: time_format(m.used_time),
    }

    column_searchable_list = ('order_number',)
    column_default_sort = ('id', False)
    column_exclude_list = ('job',)
    form_excluded_columns = ('job',)
    column_details_exclude_list = ('job',)

class UsedOrderAdmin(OrderAdmin):
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used == True)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == True)

class UnusedStandardOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==False, self.model.type == Order.Type.STANDARD)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == False, self.model.type == Order.Type.STANDARD)

class UnusedFastTrackOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==False, self.model.type == Order.Type.FAST_TRACK)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used==False, self.model.type == Order.Type.FAST_TRACK)

admin.add_view(SuccessJobAdmin(Job, db.session, endpoint="admin.success_jobs", name=u"过往数据下载"))
admin.add_view(UnusedStandardOrderAdmin(Order, db.session, endpoint="admin.unused_standard_order", name=u"未使用标准订单"))
admin.add_view(UnusedFastTrackOrderAdmin(Order, db.session, endpoint="admin.unused_fast_track_order", name=u"未使用快递订单"))
admin.add_view(UsedOrderAdmin(Order, db.session, endpoint="admin.used_order", name=u"已生成订单"))
admin.add_view(FailedJobAdmin(Job, db.session, endpoint="admin.failed_jobs", name=u"错误记录"))
admin.add_link(MenuLink(name=u"回到主界面", endpoint="front_end.index"))
