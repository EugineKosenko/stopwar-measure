from flask import Flask
from config import Config
from model import db
from flask import render_template
from model import Measurement
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import Result



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
@app.route("/")
def index():
    measurements = Measurement.query
    measurements = measurements.filter_by(proto='tcp', is_active=True)
    measurements = measurements.filter(Measurement.stamp != None)
    measurements = measurements.order_by(Measurement.trace_access.desc())
    measurements = measurements.order_by(Measurement.ssl_access.desc())
    measurements = measurements.order_by(Measurement.topic.asc())
    measurements = measurements.order_by(Measurement.resource.asc())
    measurements = measurements.all()
    return render_template('index.html', measurements=measurements)
