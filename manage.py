
import click
from flask.cli import with_appcontext
from extensions import db
from app import create_app

app = create_app()

@click.command(name='init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    db.create_all()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

if __name__ == '__main__':
    app.run()
