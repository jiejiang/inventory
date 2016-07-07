# -*- coding: utf-8 -*-
__author__ = 'jie'

from flask_admin import Admin, AdminIndexView, expose

class MyAdminIndexView(AdminIndexView):
    def is_visible(self):
        return False

admin = Admin(name=u"Admin", template_mode='bootstrap3', index_view=MyAdminIndexView(endpoint="admin"))

from . import views