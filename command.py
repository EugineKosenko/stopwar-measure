from flask import Flask
from config import Config
from flask.cli import AppGroup
import click
from model import db, Measurement
import yaml
from datetime import datetime, timedelta
from ripe.atlas.cousteau import Ping, Traceroute, Sslcert, AtlasSource, AtlasCreateRequest, MeasurementRequest
from sqlalchemy import or_
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import Result
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
measurement = AppGroup('measurement')
app.cli.add_command(measurement)
@measurement.command('add')
@click.argument('name')
@click.argument('address')
def add_measurement(name, address):
    Measurement.add(name, address)
@measurement.command('file')
@click.argument('name')
def add_file(name):
    with open(name, 'r') as f:
        data = yaml.safe_load(f)
        for topic in data['topics']:
            for resource in topic['resources']:
                for target in resource['targets']:
                    for dest in parse_target(target):
                        db.session.add(Measurement.make(
                            topic['name'], resource['name'],
                            dest['address'], dest['proto']))
        db.session.commit()
@measurement.command('execute')
def execute():
    measurements = Measurement.query.filter_by(proto='tcp', is_active=True)
    measurements = measurements.filter(
        or_(Measurement.error != None,
            Measurement.stamp == None,
            Measurement.stamp < datetime.now() - timedelta(hours=6)))

    source = AtlasSource(
        type='country',
        value='RU',
        requested=10)

    for measurement in measurements.all():
        trace = Traceroute(
            af=4,
            target=measurement.address,
            protocol='TCP',
            description=f"Trace %s" % measurement.address)
        ssl = Sslcert(
            af=4,
            target=measurement.address,
            description=f"SSL %s" % measurement.address)

        request = AtlasCreateRequest(
            start_time=datetime.utcnow() + timedelta(seconds=1),
            key="<key>",
            measurements=[trace, ssl],
            sources=[source],
            is_oneoff=True)

        is_success, response = request.create()
        print(measurement.address, is_success)
        if is_success:
            measurement.trace_id = response['measurements'][0]
            measurement.ssl_id = response['measurements'][1]
            measurement.stamp = datetime.now()
            measurement.error = None
        else:
            measurement.error = response
            print(response)
        db.session.add(measurement)

    db.session.commit()
@measurement.command('show')
def show():
    measurements = Measurement.query.filter_by(proto='tcp', is_active=True).all()

    for measurement in measurements:
        is_success, results = AtlasResultsRequest(msm_id=measurement.trace_id).create()
        
        if is_success:
            reachable = 0
            for result in results:
                result = Result.get(result)
                if result.is_success:
                    reachable += 1
        
            if len(results) == 0:
                measurement.trace_access = None
            else:
                measurement.trace_access = int(reachable / len(results) * 100)
        is_success, results = AtlasResultsRequest(msm_id=measurement.ssl_id).create()
        
        if is_success:
            unreachable = 0
            for result in results:
                result = Result.get(result)
                if result.response_time is None:
                    unreachable += 1
        
            if len(results) == 0:
                measurement.ssl_access = None
            else:
                measurement.ssl_access = int((1 - unreachable / len(results)) * 100)

        db.session.add(measurement)

        print(measurement.address, measurement.trace_access, measurement.ssl_access)

        db.session.commit()
def parse_target(source):
    result = []
    if re.search(r"^http", source):
        m = re.fullmatch(r"(http|https)://([a-z0-9\-\.]+)(.*)", source)
        if m[1] == 'http':
            port = 80
        elif m[1] == 'https':
            port = 443
        else:
            raise "Неправильный протокол"
        result.append({
            'address': m[2],
            'proto': 'tcp'})
    else:
        m = re.fullmatch(r"([^ ]+) \(([^\)]+)\)", source)
        address, ports = m[1], m[2].split(", ")
        for p in ports:
            port, proto = p.split("/")
            if proto in ['http', 'https']:
                proto = 'tcp'
            result.append({
                'address': address,
                'proto': proto})
        pass
    return result
