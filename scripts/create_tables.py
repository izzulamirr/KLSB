"""Create DB tables for the app using the currently configured SQLALCHEMY_DATABASE_URI.

Usage (PowerShell):
  # set your DB env vars first (example)
  $env:DB_USER = 'mysqluser'; $env:DB_PASS = 'mysqlpass'; $env:DB_NAME = 'klsb_db'; $env:DB_HOST = '127.0.0.1'
  python scripts/create_tables.py

The script prints the active SQLALCHEMY_DATABASE_URI and lists created tables.
"""
from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print('Using SQLALCHEMY_DATABASE_URI =', uri)
    print('Creating tables (this is safe when using create_all on a new DB) ...')
    db.create_all()
    inspector = inspect(db.engine)
    print('Tables now in database:', inspector.get_table_names())
