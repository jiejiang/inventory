# -*- coding: utf-8 -*-
from markupsafe import Markup

__author__ = 'jie'

from flask_admin.contrib import sqla
from flask_admin.menu import MenuLink
from flask_admin.model.form import InlineFormAdmin
from sqlalchemy import func, desc, or_

from .. import db
from . import admin
from ..models import Order, Job, ProductInfo, ProductCountInfo, Retraction
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
    column_default_sort = ('creation_time', True)

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
    column_exclude_list = ('job',)
    form_excluded_columns = ('job',)
    column_details_exclude_list = ('job',)

class UsedOrderAdmin(OrderAdmin):
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True
    column_default_sort = ('used_time', True)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used == True)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == True)

class UnusedStandardOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False
    column_default_sort = ('order_number', False)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==False, self.model.type == Order.Type.STANDARD)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == False, self.model.type == Order.Type.STANDARD)

class UnusedFastTrackOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False
    column_default_sort = ('order_number', False)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==False, self.model.type == Order.Type.FAST_TRACK)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used==False, self.model.type == Order.Type.FAST_TRACK)

class UnretractedOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_default_sort = ('used_time', True)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==True, self.model.retraction_id == None)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used==True, self.model.retraction_id == None)

class RetractedOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_default_sort = ('used_time', True)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==True, self.model.retraction_id <> None)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used==True, self.model.retraction_id <> None)

class ProductCountInfoInlineModelForm(InlineFormAdmin):
    column_labels = dict(count=u"箱件数", gross_weight_per_box=u"每箱毛重(KG)")

class ProductInfoAdmin(sqla.ModelView):
    #inline_models = [(ProductCountInfo, dict(form_columns=['count']))]
    inline_models = (ProductCountInfoInlineModelForm(ProductCountInfo),)
    column_list = ('name', 'net_weight', 'count_infos', 'price_per_kg', 'full_name', 'deprecated')

    column_labels = dict(name=u"商品名称", net_weight=u"每件净重(KG)", count_infos=u"箱件数 / 毛重",
                         price_per_kg=u"每千克价格(KG)", full_name=u"全称", deprecated=u"弃用")
    can_view_details = True
    column_default_sort = ('name', False)
    column_searchable_list = ('name', 'full_name')

    def _show_count_infos(view, context, model, name):
        return Markup(model.count_info_string)

    column_formatters = {
        'count_infos': _show_count_infos
    }

    def on_model_change(self, form, model, is_created):
        model.name = "".join(model.name.strip().split())

class RetractionAdmin(sqla.ModelView):
    list_template = "admin/retraction/list.html"
    can_create = False
    can_edit = False
    can_delete = False

    column_formatters = {
        'timestamp': lambda v, c, m, p: time_format(m.timestamp),
    }

admin.add_view(SuccessJobAdmin(Job, db.session, endpoint="admin.success_jobs", name=u"生成订单下载"))
admin.add_view(RetractionAdmin(Retraction, db.session, endpoint="admin.success_retraction", name=u"提取订单下载"))
admin.add_view(ProductInfoAdmin(ProductInfo, db.session, endpoint="admin.product_info", name=u"商品信息"))
admin.add_view(UnusedStandardOrderAdmin(Order, db.session, endpoint="admin.unused_standard_order", name=u"未使用标准订单"))
admin.add_view(UnusedFastTrackOrderAdmin(Order, db.session, endpoint="admin.unused_fast_track_order", name=u"未使用快递订单"))
admin.add_view(UsedOrderAdmin(Order, db.session, endpoint="admin.used_order", name=u"已生成订单"))
admin.add_view(UnretractedOrderAdmin(Order, db.session, endpoint="admin.unretracted_order", name=u"未提取订单"))
admin.add_view(RetractedOrderAdmin(Order, db.session, endpoint="admin.retracted_order", name=u"已提取订单"))
admin.add_view(FailedJobAdmin(Job, db.session, endpoint="admin.failed_jobs", name=u"错误记录"))
admin.add_link(MenuLink(name=u"回到主界面", endpoint="front_end.index"))
