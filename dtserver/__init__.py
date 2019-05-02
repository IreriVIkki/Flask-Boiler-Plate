from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_migrate import Migrate
import dailymotion

# Init app
app = Flask(__name__)

# Init cors
CORS(app)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vikki:sasawa@localhost:5432/dt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# Init Dailymotion
daily_motion = dailymotion.Dailymotion()

# Init db
db = SQLAlchemy(app)

# Init ma
ma = Marshmallow(app)

# Init migrate
migrate = Migrate(app, db)

# Import Routes after all is initialized
if True:
    from dtserver import routes
