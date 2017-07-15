# -*- coding: utf-8 -*-
from markupsafe import Markup

__author__ = 'jie'

from flask import redirect, url_for, flash
from flask_admin.contrib import sqla
from flask_admin.menu import MenuLink
from flask_admin.model.form import InlineFormAdmin
from sqlalchemy import func, desc, or_
from flask_user import current_user
from flask_admin.actions import action

from .. import db
from . import admin
from ..models import Order, Job, ProductInfo, ProductCountInfo, Retraction
from ..util import time_format

class LoginRequiredModelView(sqla.ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("user.login"))

class JobAdmin(LoginRequiredModelView):
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
    column_searchable_list = ('uuid', 'creation_time', 'issuer')
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

class OrderAdmin(LoginRequiredModelView):
    def _show_type(view, context, model, name):
        return model.type_name

    column_formatters = {
        'type': _show_type,
        'upload_time': lambda v, c, m, p: time_format(m.upload_time),
        'used_time': lambda v, c, m, p: time_format(m.used_time),
    }

    column_searchable_list = ('order_number', 'receiver_id_number', 'receiver_name')
    column_exclude_list = ('job',)
    form_excluded_columns = ('job',)
    column_details_exclude_list = ('job',)

class UsedOrderAdmin(OrderAdmin):
    list_template = "admin/order/list.html"
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True
    column_default_sort = ('used_time', True)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used == True)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == True)

    @action('reuse', u"回收单号", u"您确定需要回收这些单号？")
    def action_approve(self, ids):
        try:
            order_numbers = []
            query = Order.query.filter(Order.id.in_(ids)).order_by(desc(Order.used_time))
            for order in query.all():
                order_numbers.append(order.order_number)
                if order.retraction_id:
                    raise Exception, u"无法回收已提取单号: %s" % order.order_number
                order.make_reusable()
            db.session.commit()
            flash(u"如下单号已经回收：[%s]" % ", ".join(order_numbers))
        except Exception, inst:

            flash(u"无法回收单号：[%s]。错误如下：\n%s" % (", ".join(order_numbers), str(inst)), "error")


class UnusedOrderAdmin(OrderAdmin):
    can_create = False
    can_edit = False
    column_default_sort = ('order_number', False)

    def get_query(self):
        return self.session.query(self.model).filter(self.model.used==False, self.model.type == Order.Type.YUNDA)

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(self.model.used == False, self.model.type == Order.Type.YUNDA)


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

class ProductInfoAdmin(LoginRequiredModelView):
    #inline_models = [(ProductCountInfo, dict(form_columns=['count']))]
    #inline_models = (ProductCountInfoInlineModelForm(ProductCountInfo),)
    column_list = (
        'name', 'net_weight', 'gross_weight', 'unit_price', 'unit_per_item', 'tax_code', 'full_name', 'deprecated')

    column_labels = dict(name=u"商品名称", net_weight=u"每件净重(KG)", count_infos=u"箱件数 / 毛重  -- 已作废",
                         price_per_kg=u"每千克价格(KG) -- 已作废", full_name=u"全称(设置后无法修改)", deprecated=u"弃用",
                         unit_price=u"单价", gross_weight=u"每件毛重(KG)", tax_code=u"商品税号", billing_unit=u"计费单位",
                         billing_unit_code=u"计费单位代码", unit_per_item=u"单个物品申报数量", specification=u"规格/型号",
                         bc_product_code=u"BC商品编码", bc_specification=u"BC商品规格型号",
                         bc_second_quantity=u"BC第二数量", bc_measurement_unit=u"BC计量单位",
                         bc_second_measurement_unit=u"BC第二计量单位", )
    can_view_details = True
    column_default_sort = ('name', False)
    column_searchable_list = ('name', 'full_name')
    form_excluded_columns = ('price_per_kg', 'count_infos')

    def _show_count_infos(view, context, model, name):
        return Markup(model.count_info_string)

    column_formatters = {
        'count_infos': _show_count_infos
    }

    def on_model_change(self, form, model, is_created):
        model.name = "".join(model.name.strip().split())
        if not is_created:
            if form.full_name.object_data <> form.full_name.data:
                model.full_name = form.full_name.object_data
        else:
            model.full_name = "".join(model.full_name.strip().split())


class RetractionAdmin(LoginRequiredModelView):
    list_template = "admin/retraction/list.html"
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ('uuid', 'timestamp')
    column_default_sort = ('timestamp', True)

    column_formatters = {
        'timestamp': lambda v, c, m, p: time_format(m.timestamp),
    }

admin.add_view(SuccessJobAdmin(Job, db.session, endpoint="admin.success_jobs", name=u"生成订单下载"))
admin.add_view(RetractionAdmin(Retraction, db.session, endpoint="admin.success_retraction", name=u"提取订单下载"))
admin.add_view(ProductInfoAdmin(ProductInfo, db.session, endpoint="admin.product_info", name=u"商品信息"))
admin.add_view(UnusedOrderAdmin(Order, db.session, endpoint="admin.unused_standard_order", name=u"未使用韵达订单"))
admin.add_view(UsedOrderAdmin(Order, db.session, endpoint="admin.used_order", name=u"已生成订单"))
admin.add_view(UnretractedOrderAdmin(Order, db.session, endpoint="admin.unretracted_order", name=u"未提取订单"))
admin.add_view(RetractedOrderAdmin(Order, db.session, endpoint="admin.retracted_order", name=u"已提取订单"))
admin.add_view(FailedJobAdmin(Job, db.session, endpoint="admin.failed_jobs", name=u"错误记录"))
admin.add_link(MenuLink(name=u"回到主界面", endpoint="front_end.index"))
