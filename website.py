#!/usr/bin/env python

import gspread
import time
import os.path

from functools import wraps
from flask import Flask, render_template, request, Response, send_file
from oauth2client.service_account import ServiceAccountCredentials

from report import make_pdf_file

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    with open(os.path.join(os.path.dirname(__file__), "users.txt")) as f:
        for l in f:
            l = l.strip()
            if l == ("%s:%s" % (username, password)):
                return True
    return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


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


def get_data():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(os.path.dirname(__file__), 'Contacalorie-cef2fe8fdd6c.json'), scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("DBContacalorieMaiano").sheet1

    # Extract and print all of the values
    list_of_hashes = sheet.get_all_records()
    res = []
    for d in list_of_hashes:
        res.append(Datum.from_dict(d))
    return res


class Datum(object):
    def __init__(self):
        self.data = None
        self.gas_generale = None
        self.gas_pp = None
        self.gas_sp = None
        self.gas_mp = None
        self.calorie_pp_zona_giorno = None
        self.calorie_pp_zona_notte = None
        self.calorie_sp = None
        self.calorie_mp = None
        self.calorie_mg = None
        self.calorie_h2o_calda = None
        self.h2o_calda_andata_pp = None
        self.h2o_calda_ricircolo_pp = None
        self.h2o_calda_andata_sp = None
        self.h2o_calda_ricircolo_sp = None
        self.h2o_calda_andata_mp = None
        self.h2o_calda_ricircolo_mp = None
        self.h2o_calda_andata_mg = None
        self.h2o_calda_ricircolo_mg = None
        self.costo_bolletta = None

    @staticmethod
    def from_dict(d):
        r = Datum()
        r.data = d['Data di rilevamento']
        r.gas_generale = d['Contatore gas generale']
        r.gas_pp = d['Contatore gas primo piano']
        r.gas_sp = d['Contatore gas secondo piano']
        r.gas_mp = d['Contatore gas mansarda piccola']
        r.calorie_pp_zona_giorno = d['Contatore calorie primo piano zona giorno']
        r.calorie_pp_zona_notte = d['Contatore calorie primo piano zona notte']
        r.calorie_sp = d['Contatore calorie secondo piano']
        r.calorie_mp = d['Contatore calorie mansarda piccola']
        r.calorie_mg = d['Contatore calorie mansarda grande']
        r.calorie_h2o_calda = d['Contatore calorie acqua calda']
        r.h2o_calda_andata_pp = d['Contatore H2O calda andata primo piano']
        r.h2o_calda_ricircolo_pp = d['Contatore H2O ricircolo primo piano']
        r.h2o_calda_andata_sp = d['Contatore H2O calda andata secondo piano']
        r.h2o_calda_ricircolo_sp = d['Contatore H2O ricircolo secondo piano']
        r.h2o_calda_andata_mp = d['Contatore H2O calda andata mansada piccola']
        r.h2o_calda_ricircolo_mp = d['Contatore H2O ricircolo mansarda piccola']
        r.h2o_calda_andata_mg = d['Contatore H2O calda andata mansarda grande']
        r.h2o_calda_ricircolo_mg = d['Contatore H2O ricircolo mansarda grande']
        r.costo_bolletta = d['Costo totale bolletta gas']
        return r

class Ripartizione(object):
    def __init__(self, date=None, pp=None, sp=None, mp=None, mg=None):
        self.date = date
        self.pp = pp
        self.sp = sp
        self.mp = mp
        self.mg = mg

    def totale(self):
        return self.pp + self.sp + self.mp + self.mg

    def __str__(self):
        return "PP: %s\nSP: %s\nMP: %s\nMG: %s\n=========\nTOT: %s" % \
            (self.pp, self.sp, self.mp, self.mg, self.totale())


def partition(d1, d2):
    date = (d1.data, d2.data)
    diff_gas_generale = d2.gas_generale - d1.gas_generale

    if diff_gas_generale == 0:
        return Ripartizione(date, 0,0,0,0)

    diff_gas_pp = d2.gas_pp - d1.gas_pp
    diff_gas_sp = d2.gas_sp - d1.gas_sp
    diff_gas_mp = d2.gas_mp - d1.gas_mp

    euro_per_mc = d2.costo_bolletta / diff_gas_generale
    gas_h2o_calda = diff_gas_generale - diff_gas_mp - diff_gas_sp - diff_gas_pp
    costo_h2o_calda = euro_per_mc * gas_h2o_calda

    diff_calorie_pp_zona_giorno = d2.calorie_pp_zona_giorno - d1.calorie_pp_zona_giorno
    diff_calorie_pp_zona_notte = d2.calorie_pp_zona_notte - d1.calorie_pp_zona_notte
    diff_calorie_pp = diff_calorie_pp_zona_giorno + diff_calorie_pp_zona_notte
    diff_calorie_sp = d2.calorie_sp - d1.calorie_sp
    diff_calorie_mp = d2.calorie_mp - d1.calorie_mp
    diff_calorie_mg = d2.calorie_mg - d1.calorie_mg

    totale_calorie_riscaldamento = diff_calorie_pp + diff_calorie_sp + diff_calorie_mg + diff_calorie_mp
    diff_calorie_h2o_calda = d2.calorie_h2o_calda - d1.calorie_h2o_calda

    consumo_h2o_pp = (d2.h2o_calda_andata_pp - d1.h2o_calda_andata_pp) - (d2.h2o_calda_ricircolo_pp - d1.h2o_calda_ricircolo_pp)
    consumo_h2o_sp = (d2.h2o_calda_andata_sp - d1.h2o_calda_andata_sp) - (d2.h2o_calda_ricircolo_sp - d1.h2o_calda_ricircolo_sp)
    consumo_h2o_mp = (d2.h2o_calda_andata_mp - d1.h2o_calda_andata_mp) - (d2.h2o_calda_ricircolo_mp - d1.h2o_calda_ricircolo_mp)
    consumo_h2o_mg = (d2.h2o_calda_andata_mg - d1.h2o_calda_andata_mg) - (d2.h2o_calda_ricircolo_mg - d1.h2o_calda_ricircolo_mg)
    consumo_totale_h2o = consumo_h2o_mg + consumo_h2o_mp + consumo_h2o_pp + consumo_h2o_sp

    ripartizione_pp = diff_calorie_pp + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_pp
    ripartizione_sp = diff_calorie_sp + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_sp
    ripartizione_mp = diff_calorie_mp + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_mp
    ripartizione_mg = diff_calorie_mg + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_mg

    res = Ripartizione()
    res.date = date
    res.pp = euro_per_mc * diff_gas_pp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_pp
    res.sp = euro_per_mc * diff_gas_sp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_sp
    res.mp = euro_per_mc * diff_gas_mp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_mp
    res.mg = costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_mg

    return res


if __name__ == '__main__':
    app.run(debug=True)
