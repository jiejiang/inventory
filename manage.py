__author__ = 'jie'

import os, sys

from app import app
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

from app import db
from app.models import City
from app.main.postorder import xls_to_orders, read_order_numbers, retract_from_order_numbers

def make_shell_context():
    return dict(app=app, db=db)

if __name__ == '__main__':
    manager = Manager(app)

    @manager.command
    def populate(filename):
        "Populate"
        City.populate(filename)

    @manager.command
    def find_province(name):
        "Find province"
        province, current = City.find_province(name)
        if province:
            print province.name, province.type
            print current.name, current.type
        else:
            print "Not Found"

    @manager.command
    def find_province_path(name):
        cities = City.find_province_path(name)
        if not cities:
            print "Not Found"
            exit(1)
        for city in cities:
            print city.name, city.type
        province, city, address_header = City.normalize_province_path(cities)
        print province, city, address_header

    @manager.command
    def batch(input, output, tmpdir):
        if not os.path.exists(output):
            os.makedirs(output)
        try:
            xls_to_orders(input, output, tmpdir)
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            print >> sys.stderr, inst.message.encode('utf-8')

    @manager.command
    def retract(input, output, route):
        try:
            if not route in app.config['ROUTE_CONFIG']:
                raise Exception, "No route"
            route_config = app.config['ROUTE_CONFIG'][route]
            order_numbers = read_order_numbers(input)
            retract_from_order_numbers(app.config['DOWNLOAD_FOLDER'], order_numbers, output, route_config)
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            print >> sys.stderr, inst.message.encode('utf-8')

    migrate = Migrate(app, db)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.add_command('db', MigrateCommand)
    manager.add_command("runserver", Server(host="0.0.0.0"))
    manager.run()
