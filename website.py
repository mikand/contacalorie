import os
import datetime

from flask import Flask, render_template, send_file, jsonify, request

from report import make_pdf_file
from utils import requires_auth
from calorie import (FIELDS, LABELS, Reading, Session, format_date_italian,
                     get_readings, grouped_fields, split_costs)

app = Flask(__name__)

# Keys are the identifiers used in URLs, JSON and CostSplit attributes;
# values are what the resident sees.
APARTMENTS = {'floor_1': 'Primo Piano', 'floor_2': 'Secondo Piano', 'floor_3': 'Terzo Piano'}


@app.errorhandler(ValueError)
def bad_request(e):
    """Every parse/validation failure surfaces as a readable message instead
    of a stack trace or a raw SQL statement."""
    return jsonify({'error': str(e)}), 400


def parse_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Data non valida: %r (formato atteso AAAA-MM-GG)" % value)


def parse_values(payload):
    """Pull every meter out of a request body, or say exactly what is wrong."""
    values = {}
    for field in FIELDS:
        value = payload.get(field)
        if value is None or value == '':
            raise ValueError("Campo mancante: %s" % LABELS[field])
        try:
            values[field] = float(value)
        except (TypeError, ValueError):
            raise ValueError("Valore non numerico per %s: %r" % (LABELS[field], value))
    return values


def to_dict(reading):
    return dict({'date': reading.date.isoformat()},
                **{f: getattr(reading, f) for f in FIELDS})


@app.route('/')
@requires_auth
def index():
    return render_template('index.html',
                           fields=FIELDS,
                           groups=grouped_fields(),
                           labels=LABELS,
                           copyright_date=datetime.date.today().year)


@app.route('/report/<string:apartment>/<string:date1>/<string:date2>')
@requires_auth
def report(apartment, date1, date2):
    if apartment not in APARTMENTS:
        raise ValueError("Appartamento sconosciuto: %r" % apartment)
    start, end = parse_date(date1), parse_date(date2)

    with Session() as session:
        r1 = session.get(Reading, start)
        r2 = session.get(Reading, end)

    if r1 is None or r2 is None:
        return jsonify({'error': 'Rilevamento non trovato'}), 404

    # The amount is recomputed here rather than taken from the URL, so the
    # notice can never disagree with what the site shows.
    split = split_costs(r1, r2)
    if split.is_error():
        return jsonify({'error': "Impossibile calcolare la ripartizione: %s" % split.error}), 400

    name = APARTMENTS[apartment]
    return send_file(make_pdf_file(name, getattr(split, apartment), (start, end)),
                     mimetype='application/pdf',
                     download_name="Ripartizione %s %s.pdf" % (name, end.isoformat()))


@app.route('/api/cost-splits', methods=['GET'])
@requires_auth
def api_cost_splits():
    readings = get_readings()
    splits = []
    for previous, current in zip(readings, readings[1:]):
        split = split_costs(previous, current)
        splits.append({
            'from': previous.date.isoformat(),
            'to': current.date.isoformat(),
            'error': split.error,
            'floor_1': split.floor_1,
            'floor_2': split.floor_2,
            'floor_3': split.floor_3,
            'total': None if split.is_error() else split.total(),
            # The bill the period was split from: the site shows it next to
            # the total so a split that does not add up is visible at a glance.
            'bill_cost': current.bill_cost,
            # Every intermediate of the calculation, for the help dialog.
            'steps': split.steps,
        })
    splits.reverse()  # most recent period first
    return jsonify(splits)


@app.route('/api/readings', methods=['GET'])
@requires_auth
def api_get_readings():
    return jsonify([to_dict(reading) for reading in get_readings()])


@app.route('/api/readings/<string:reading_date>', methods=['GET'])
@requires_auth
def api_get_reading(reading_date):
    with Session() as session:
        reading = session.get(Reading, parse_date(reading_date))
        if reading is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        return jsonify(to_dict(reading))


@app.route('/api/readings', methods=['POST'])
@requires_auth
def api_create_reading():
    payload = request.get_json(silent=True) or {}
    date = parse_date(payload.get('date'))
    values = parse_values(payload)

    with Session() as session:
        if session.get(Reading, date) is not None:
            return jsonify({'error': "Esiste già un rilevamento per il %s"
                                     % format_date_italian(date)}), 409
        session.add(Reading(date=date, **values))
        session.commit()

    return jsonify({'message': 'Rilevamento creato'}), 201


@app.route('/api/readings/<string:reading_date>', methods=['PUT'])
@requires_auth
def api_update_reading(reading_date):
    date = parse_date(reading_date)
    # The date is the primary key and comes from the URL only: any 'date' in
    # the body is ignored, so the key can never drift from the record.
    values = parse_values(request.get_json(silent=True) or {})

    with Session() as session:
        reading = session.get(Reading, date)
        if reading is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        for field, value in values.items():
            setattr(reading, field, value)
        session.commit()

    return jsonify({'message': 'Rilevamento aggiornato'}), 200


@app.route('/api/readings/<string:reading_date>', methods=['DELETE'])
@requires_auth
def api_delete_reading(reading_date):
    with Session() as session:
        reading = session.get(Reading, parse_date(reading_date))
        if reading is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        session.delete(reading)
        session.commit()

    return jsonify({'message': 'Rilevamento eliminato'}), 200


if __name__ == '__main__':
    # ponytail: debug is opt-in (FLASK_DEBUG=1) so the Werkzeug console is
    # never one stray run away from being served.
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
