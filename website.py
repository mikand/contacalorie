import time
import os

from datetime import datetime
from sqlalchemy import extract, and_

from flask import Flask, render_template, send_file
from flask_sqlalchemy import SQLAlchemy

from report import HourReport, build_pdf_report
from utils import requires_auth

app = Flask(__name__)
wd = os.path.dirname(os.path.realpath(__file__))
dbpath = os.path.join(wd, 'cianna.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbpath
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class WorkPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    workplace = db.Column(db.String(255), nullable=False)

class WorkPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(255), nullable=False)

if not os.path.exists(dbpath):
    db.create_all()


@app.route('/')
@requires_auth
def index():
    workplaces = WorkPlace.query.all()
    work_periods = WorkPeriod.query.all()

    workplaces_map = {wp.name : wp.color for wp in workplaces}

    return render_template('index.html',
                           copyright_date=time.strftime('%Y'),
                           workplaces=workplaces_map,
                           work_periods=work_periods)

@app.route('/newperiod/<int:start>/<int:end>/<string:workplace>')
@requires_auth
def new_period(start, end, workplace):
    p = WorkPeriod(start=datetime.fromtimestamp(start),
                   end=datetime.fromtimestamp(end),
                   workplace=workplace)
    db.session.add(p)
    db.session.commit()
    return str(p.id)

@app.route('/newworkplace/<string:name>/<string:color>')
@requires_auth
def new_workplace(name, color):
    p = WorkPlace(name=name, color=color)
    db.session.add(p)
    db.session.commit()
    return 'OK'

@app.route('/chperiod/<int:id_>/<int:start>/<int:end>')
@requires_auth
def change_period(id_, start, end):
    p = WorkPeriod.query.filter_by(id=id_).first()
    p.start = datetime.fromtimestamp(start)
    p.end = datetime.fromtimestamp(end)
    db.session.add(p)
    db.session.commit()
    return "OK"

@app.route('/editperiod/<int:id_>/<int:start>/<int:end>/<string:workplace>')
@requires_auth
def edit_period(id_, start, end, workplace):
    p = WorkPeriod.query.filter_by(id=id_).first()
    p.start = datetime.fromtimestamp(start)
    p.end = datetime.fromtimestamp(end)
    p.workplace = workplace
    db.session.add(p)
    db.session.commit()
    return "OK"

@app.route('/rmperiod/<int:id_>')
@requires_auth
def remove_period(id_):
    p = WorkPeriod.query.filter_by(id=id_).first()
    db.session.delete(p)
    db.session.commit()
    return "OK"

@app.route('/get_pdf_report/<int:date>')
@requires_auth
def get_pdf_report(date):
    date = datetime.fromtimestamp(date)
    hr = HourReport(date.month, date.year)
    wps = WorkPeriod.query.filter(and_(extract('month', WorkPeriod.start)==date.month,
                                       extract('year', WorkPeriod.start)==date.year)).all()
    for wp in wps:
        day = wp.start.day
        p = wp.workplace
        if p not in hr.workplaces:
            hr.workplaces.append(p)
        hr.worked_hours.append((day, p, wp.start.hour, wp.start.minute, wp.end.hour, wp.end.minute))

    hr.workplaces.sort()
    pdf_out = build_pdf_report(hr)
    return send_file(pdf_out,
                     attachment_filename='%d_%d_Foglio_Ore_Gianna.pdf' % (date.month, date.year),
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
