import os
import datetime

from flask import Flask, render_template, send_file, jsonify, request

from report import make_pdf_file
from utils import requires_auth
from calorie import (FIELDS, LABELS, Datum, Session, format_date_italian,
                     get_data, partition)

app = Flask(__name__)

APPARTAMENTI = {'pp': 'Primo Piano', 'sp': 'Secondo Piano', 'tp': 'Terzo Piano'}


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


def to_dict(record):
    return dict({'data': record.data.isoformat()},
                **{f: getattr(record, f) for f in FIELDS})


@app.route('/')
@requires_auth
def index():
    return render_template('index.html',
                           fields=FIELDS,
                           labels=LABELS,
                           copyright_date=datetime.date.today().year)


@app.route('/report/<string:appartamento>/<string:data1>/<string:data2>')
@requires_auth
def report(appartamento, data1, data2):
    if appartamento not in APPARTAMENTI:
        raise ValueError("Appartamento sconosciuto: %r" % appartamento)
    date1, date2 = parse_date(data1), parse_date(data2)

    with Session() as session:
        d1 = session.get(Datum, date1)
        d2 = session.get(Datum, date2)

    if d1 is None or d2 is None:
        return jsonify({'error': 'Rilevamento non trovato'}), 404

    # The amount is recomputed here rather than taken from the URL, so the
    # notice can never disagree with what the site shows.
    rip = partition(d1, d2)
    if rip.is_error():
        return jsonify({'error': "Impossibile calcolare la ripartizione: %s" % rip.error}), 400

    nome = APPARTAMENTI[appartamento]
    return send_file(make_pdf_file(nome, getattr(rip, appartamento), (date1, date2)),
                     mimetype='application/pdf',
                     download_name="Ripartizione %s %s.pdf" % (nome, date2.isoformat()))


@app.route('/api/ripartizioni', methods=['GET'])
@requires_auth
def api_ripartizioni():
    data = get_data()
    rips = []
    for prev, curr in zip(data, data[1:]):
        rip = partition(prev, curr)
        rips.append({
            'da': prev.data.isoformat(),
            'a': curr.data.isoformat(),
            'error': rip.error,
            'pp': rip.pp,
            'sp': rip.sp,
            'tp': rip.tp,
            'totale': None if rip.is_error() else rip.totale(),
        })
    rips.reverse()  # most recent period first
    return jsonify(rips)


@app.route('/api/data', methods=['GET'])
@requires_auth
def api_get_data():
    return jsonify([to_dict(record) for record in get_data()])


@app.route('/api/data/<string:record_date>', methods=['GET'])
@requires_auth
def api_get_record(record_date):
    with Session() as session:
        record = session.get(Datum, parse_date(record_date))
        if record is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        return jsonify(to_dict(record))


@app.route('/api/data', methods=['POST'])
@requires_auth
def api_create_record():
    payload = request.get_json(silent=True) or {}
    date = parse_date(payload.get('data'))
    values = parse_values(payload)

    with Session() as session:
        if session.get(Datum, date) is not None:
            return jsonify({'error': "Esiste già un rilevamento per il %s"
                                     % format_date_italian(date)}), 409
        session.add(Datum(data=date, **values))
        session.commit()

    return jsonify({'message': 'Rilevamento creato'}), 201


@app.route('/api/data/<string:record_date>', methods=['PUT'])
@requires_auth
def api_update_record(record_date):
    date = parse_date(record_date)
    # The date is the primary key and comes from the URL only: any 'data' in
    # the body is ignored, so the key can never drift from the record.
    values = parse_values(request.get_json(silent=True) or {})

    with Session() as session:
        record = session.get(Datum, date)
        if record is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        for field, value in values.items():
            setattr(record, field, value)
        session.commit()

    return jsonify({'message': 'Rilevamento aggiornato'}), 200


@app.route('/api/data/<string:record_date>', methods=['DELETE'])
@requires_auth
def api_delete_record(record_date):
    with Session() as session:
        record = session.get(Datum, parse_date(record_date))
        if record is None:
            return jsonify({'error': 'Rilevamento non trovato'}), 404
        session.delete(record)
        session.commit()

    return jsonify({'message': 'Rilevamento eliminato'}), 200


if __name__ == '__main__':
    # ponytail: debug is opt-in (FLASK_DEBUG=1) so the Werkzeug console is
    # never one stray run away from being served.
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
