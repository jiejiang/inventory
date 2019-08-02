__author__ = 'jie'

import os, sys

from app import app
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

from app import db
from app.models import City, Order
from app.main.postorder import xls_to_orders, read_order_numbers, retract_from_order_numbers, \
    generate_tickets_from_mapping_file

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
            print province.name, province.typeda
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
            print city.id, city.name, city.type
        province, city, address_header = City.normalize_province_path(cities)
        print province, city, address_header

    @manager.command
    def change_city_name(id, old_name, new_name):
        id = int(id)
        city = City.query.get(id)
        if not city:
            print >> sys.stderr, "Cannot find city with id: %d" % id
            return
        if not city.name == old_name:
            print >> sys.stderr, "City name %s mismatch: %s" % (city.name, old_name)
            return
        city.name = new_name
        db.session.commit()

    @manager.command
    def batch(input, output, tmpdir, order_type):
        if not os.path.exists(output):
            os.makedirs(output)
        try:
            order_type = int(order_type)
            if not order_type in Order.Type.types:
                raise Exception, "Invalid order type: %d" % order_type
            xls_to_orders(input, output, tmpdir, order_type)
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

    @manager.command
    def gen_tickets(input_xlsx, mapping_xlsx, output_dir):
        try:
            generate_tickets_from_mapping_file(input_xlsx, mapping_xlsx, output_dir)
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)

    @manager.command
    def insert_range(type, first, last, commit):
        try:
            type = int(type)
            first = int(first)
            last = int(last)
            commit = True if commit == 'commit' else False
            order_numbers = []
            if not type in Order.Type.types:
                raise Exception, "Invalid type: %d" % type
            for order_number in range(first, last+1):
                order_number = str(order_number)
                if not Order.is_order_number_valid(type, order_number):
                    raise Exception, "Invalid order number %s" % order_number
                if Order.query.filter_by(order_number=order_number).scalar() is not None:
                    raise Exception, "Order number exists: %s" % order_number
                order = Order(order_number=order_number, type=type)
                db.session.add(order)
                order_numbers.append(order_number)
            print >> sys.stderr, ",".join(order_numbers)
            print >> sys.stderr, "Total %d" % len(order_numbers)
            if commit:
                print >> sys.stderr, "Commit"
                db.session.commit()
            else:
                print >> sys.stderr, "Dry run"
        except Exception, inst:
            import traceback
            traceback.print_exc(sys.stderr)
            

    migrate = Migrate(app, db)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.add_command('db', MigrateCommand)
    manager.add_command("runserver", Server(host="0.0.0.0", port=12140))
    manager.run()
