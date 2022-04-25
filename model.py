from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class Measurement(db.Model):
    __tablename__ = 'measurements'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    resource = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    proto = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    stamp = db.Column(db.DateTime)
    ping_id = db.Column(db.Integer)
    trace_id = db.Column(db.Integer)
    ssl_id = db.Column(db.Integer)
    ping_access = db.Column(db.Float)
    lost_packs = db.Column(db.Float)
    trace_access = db.Column(db.Float)
    ssl_access = db.Column(db.Float)
    error = db.Column(db.String(255))

    __table_args__ = (db.UniqueConstraint('address', 'proto', name='unq_target'),)

    def __init__(self, topic, resource, address, proto):
        self.topic = topic
        self.resource = resource
        self.address = address
        self.proto = proto

    def __repr__(self):
        return str(self.address)

    def make(topic, resource, address, proto):
        measurements = Measurement.query.filter_by(address=address, proto=proto)
    
        if measurements.count() > 0:
            measurement = measurements.one()
            measurement.topic = topic
            measurement.resource = resource
            measurement.is_active = True
        else:
            measurement = Measurement(topic, resource, address, proto)
    
        return measurement
