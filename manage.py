__author__ = 'jie'

import os

from app import app
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

from app import db

def make_shell_context():
    return dict(app=app, db=db)

if __name__ == '__main__':
    manager = Manager(app)
    migrate = Migrate(app, db)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.add_command('db', MigrateCommand)
    manager.add_command("runserver", Server(host="0.0.0.0"))
    manager.run()
