import os

from tunga_hr_app import create_app, db
from tunga_hr_app.models.public import User

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, user=User)