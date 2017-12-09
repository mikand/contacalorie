import time

from flask import Flask, render_template, send_file

from report import make_pdf_file
from utils import requires_auth
from calorie import get_data, partition

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
            rip = partition(prev, curr)
            rips.append(rip)
    return render_template('index.html',
                           rips=rips,
                           copyright_date=time.strftime('%Y'))

@app.route('/report/<string:appartamento>/<string:costo>/<string:data1>/<string:data2>')
@requires_auth
def report(appartamento, costo, data1, data2):
    pdf_out = make_pdf_file(appartamento, costo, [data1, data2])
    return send_file(pdf_out,
                     attachment_filename='Ripartizione %s.pdf',
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
