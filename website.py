import time
import json
from datetime import datetime

from flask import Flask, render_template, send_file, jsonify, request

from report import make_pdf_file
from utils import requires_auth
from calorie import get_data, partition, Datum, Session, format_date_italian

app = Flask(__name__)

@app.route('/')
@requires_auth
def index():
    data = get_data()
    rips = []
    if len(data) >= 2:
        for i in range(len(data)-1, 0, -1):
            prev = data[i-1]
            curr = data[i]
            try:
                rip = partition(prev, curr)
                rips.append(rip)
            except Exception as e:
                print(f"Error occurred while partitioning data: {e}")
    return render_template('index.html',
                           rips=rips,
                           copyright_date=time.strftime('%Y'))

@app.route('/report/<string:appartamento>/<string:costo>/<string:data1>/<string:data2>')
@requires_auth
def report(appartamento, costo, data1, data2):
    pdf_out = make_pdf_file(appartamento, costo, [data1, data2])
    return send_file(pdf_out,
                     #download_name='Ripartizione %s.pdf',
                     mimetype='application/pdf')

# API endpoints for data management
@app.route('/api/data', methods=['GET'])
@requires_auth
def api_get_data():
    session = Session()
    data = session.query(Datum).order_by(Datum.data).all()
    session.close()

    result = []
    for row in data:
        result.append({
            'id': row.id,
            'data': format_date_italian(row.data),
            'gas_generale': row.gas_generale,
            'gas_pp': row.gas_pp,
            'gas_sp': row.gas_sp,
            'gas_tp': row.gas_tp,
            'calorie_pp_zona_giorno': row.calorie_pp_zona_giorno,
            'calorie_pp_zona_notte': row.calorie_pp_zona_notte,
            'calorie_sp': row.calorie_sp,
            'calorie_tc': row.calorie_tc,
            'calorie_tp': row.calorie_tp,
            'calorie_h2o_calda': row.calorie_h2o_calda,
            'h2o_calda_andata_pp': row.h2o_calda_andata_pp,
            'h2o_calda_ricircolo_pp': row.h2o_calda_ricircolo_pp,
            'h2o_calda_andata_sp': row.h2o_calda_andata_sp,
            'h2o_calda_ricircolo_sp': row.h2o_calda_ricircolo_sp,
            'h2o_calda_andata_tp': row.h2o_calda_andata_tp,
            'h2o_calda_ricircolo_tp': row.h2o_calda_ricircolo_tp,
            'costo_bolletta': row.costo_bolletta
        })

    return jsonify(result)

@app.route('/api/data/<path:record_id>', methods=['GET'])
@requires_auth
def api_get_record(record_id):
    session = Session()
    record = session.query(Datum).filter_by(id=record_id).first()
    session.close()

    if not record:
        return jsonify({'error': 'Record not found'}), 404

    return jsonify({
        'id': record.id,
        'data': record.data.strftime('%d/%m/%Y'),
        'gas_generale': record.gas_generale,
        'gas_pp': record.gas_pp,
        'gas_sp': record.gas_sp,
        'gas_tp': record.gas_tp,
        'calorie_pp_zona_giorno': record.calorie_pp_zona_giorno,
        'calorie_pp_zona_notte': record.calorie_pp_zona_notte,
        'calorie_sp': record.calorie_sp,
        'calorie_tc': record.calorie_tc,
        'calorie_tp': record.calorie_tp,
        'calorie_h2o_calda': record.calorie_h2o_calda,
        'h2o_calda_andata_pp': record.h2o_calda_andata_pp,
        'h2o_calda_ricircolo_pp': record.h2o_calda_ricircolo_pp,
        'h2o_calda_andata_sp': record.h2o_calda_andata_sp,
        'h2o_calda_ricircolo_sp': record.h2o_calda_ricircolo_sp,
        'h2o_calda_andata_tp': record.h2o_calda_andata_tp,
        'h2o_calda_ricircolo_tp': record.h2o_calda_ricircolo_tp,
        'costo_bolletta': record.costo_bolletta
    })

@app.route('/api/data', methods=['POST'])
@requires_auth
def api_create_record():
    data = request.get_json()

    session = Session()

    try:
        record_id = data.get('data')  # Use date as ID
        new_record = Datum(
            id=record_id,
            data=datetime.strptime(data['data'], '%d/%m/%Y').date(),
            gas_generale=data['gas_generale'],
            gas_pp=data['gas_pp'],
            gas_sp=data['gas_sp'],
            gas_tp=data['gas_tp'],
            calorie_pp_zona_giorno=data['calorie_pp_zona_giorno'],
            calorie_pp_zona_notte=data['calorie_pp_zona_notte'],
            calorie_sp=data['calorie_sp'],
            calorie_tc=data['calorie_tc'],
            calorie_tp=data['calorie_tp'],
            calorie_h2o_calda=data['calorie_h2o_calda'],
            h2o_calda_andata_pp=data['h2o_calda_andata_pp'],
            h2o_calda_ricircolo_pp=data['h2o_calda_ricircolo_pp'],
            h2o_calda_andata_sp=data['h2o_calda_andata_sp'],
            h2o_calda_ricircolo_sp=data['h2o_calda_ricircolo_sp'],
            h2o_calda_andata_tp=data['h2o_calda_andata_tp'],
            h2o_calda_ricircolo_tp=data['h2o_calda_ricircolo_tp'],
            costo_bolletta=data['costo_bolletta']
        )
        session.add(new_record)
        session.commit()
        session.close()

        return jsonify({'message': 'Record created successfully'}), 201
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/data/<path:record_id>', methods=['PUT'])
@requires_auth
def api_update_record(record_id):
    data = request.get_json()

    session = Session()
    record = session.query(Datum).filter_by(id=record_id).first()

    if not record:
        session.close()
        return jsonify({'error': 'Record not found'}), 404

    try:
        record.data = datetime.strptime(data['data'], '%d/%m/%Y').date()
        record.gas_generale = data['gas_generale']
        record.gas_pp = data['gas_pp']
        record.gas_sp = data['gas_sp']
        record.gas_tp = data['gas_tp']
        record.calorie_pp_zona_giorno = data['calorie_pp_zona_giorno']
        record.calorie_pp_zona_notte = data['calorie_pp_zona_notte']
        record.calorie_sp = data['calorie_sp']
        record.calorie_tc = data['calorie_tc']
        record.calorie_tp = data['calorie_tp']
        record.calorie_h2o_calda = data['calorie_h2o_calda']
        record.h2o_calda_andata_pp = data['h2o_calda_andata_pp']
        record.h2o_calda_ricircolo_pp = data['h2o_calda_ricircolo_pp']
        record.h2o_calda_andata_sp = data['h2o_calda_andata_sp']
        record.h2o_calda_ricircolo_sp = data['h2o_calda_ricircolo_sp']
        record.h2o_calda_andata_tp = data['h2o_calda_andata_tp']
        record.h2o_calda_ricircolo_tp = data['h2o_calda_ricircolo_tp']
        record.costo_bolletta = data['costo_bolletta']

        session.commit()
        session.close()

        return jsonify({'message': 'Record updated successfully'}), 200
    except Exception as e:
        session.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/data/<path:record_id>', methods=['DELETE'])
@requires_auth
def api_delete_record(record_id):
    print(f"Attempting to delete record with ID: {record_id}")
    session = Session()
    record = session.query(Datum).filter_by(id=record_id).first()


    if not record:
        session.close()
        return jsonify({'error': 'Record not found'}), 404

    try:
        session.delete(record)
        session.commit()
        session.close()

        return jsonify({'message': 'Record deleted successfully'}), 200
    except Exception as e:
        session.close()
        print(str(e))
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
