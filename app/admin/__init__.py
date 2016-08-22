# -*- coding: utf-8 -*-
__author__ = 'jie'

from flask import redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_user import current_user

class MyAdminIndexView(AdminIndexView):
    def is_visible(self):
        return False

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("user.login"))

admin = Admin(name=u"韵达线 Admin", template_mode='bootstrap3', index_view=MyAdminIndexView(endpoint=u"admin"))

from . import views
