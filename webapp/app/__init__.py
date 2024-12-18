from flask import Flask
app = Flask(__name__)

#from werkzeug.debug import DebuggedApplication
#app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

app.templates_auto_reload = True
app.debug = False
app.jinja_env.filters['zip'] = zip
from app import views
