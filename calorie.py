from dataclasses import dataclass
import os.path
import gspread

from oauth2client.service_account import ServiceAccountCredentials

def get_data():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(os.path.dirname(__file__), 'Contacalorie-cef2fe8fdd6c.json'), scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("DBContacalorieMaiano").sheet1

    # Extract and print all of the values
    list_of_hashes = sheet.get_all_records()
    res = []
    for d in list_of_hashes:
        datum = Datum.from_dict(d)
        res.append(datum)
    print(res)
    return res

@dataclass(eq=True)
class Datum(object):
    data = None
    gas_generale = None
    gas_pp = None
    gas_sp = None
    gas_tp = None
    calorie_pp_zona_giorno = None
    calorie_pp_zona_notte = None
    calorie_sp = None
    calorie_tc = None
    calorie_tp = None
    calorie_h2o_calda = None
    h2o_calda_andata_pp = None
    h2o_calda_ricircolo_pp = None
    h2o_calda_andata_sp = None
    h2o_calda_ricircolo_sp = None
    h2o_calda_andata_tp = None
    h2o_calda_ricircolo_tp = None
    costo_bolletta = None

    @staticmethod
    def from_dict(d):
        r = Datum()
        r.data = d['Data di rilevamento']
        r.gas_generale = d['Contatore gas generale']
        r.gas_pp = d['Contatore gas primo piano']
        r.gas_sp = d['Contatore gas secondo piano']
        r.gas_tp = d['Contatore gas terzo piano']
        r.calorie_pp_zona_giorno = d['Contatore calorie primo piano zona giorno']
        r.calorie_pp_zona_notte = d['Contatore calorie primo piano zona notte']
        r.calorie_sp = d['Contatore calorie secondo piano']
        r.calorie_tc = d['Contatore calorie taverna carlo']
        r.calorie_tp = d['Contatore calorie terzo piano']
        r.calorie_h2o_calda = d['Contatore calorie acqua calda']
        r.h2o_calda_andata_pp = d['Contatore H2O calda andata primo piano']
        r.h2o_calda_ricircolo_pp = d['Contatore H2O ricircolo primo piano']
        r.h2o_calda_andata_sp = d['Contatore H2O calda andata secondo piano']
        r.h2o_calda_ricircolo_sp = d['Contatore H2O ricircolo secondo piano']
        r.h2o_calda_andata_tp = d['Contatore H2O calda andata terzo piano']
        r.h2o_calda_ricircolo_tp = d['Contatore H2O ricircolo terzo piano']
        r.costo_bolletta = d['Costo totale bolletta gas']
        return r

class Ripartizione(object):
    def __init__(self, date=None, pp=None, sp=None, tp=None):
        self.date = date
        self.pp = pp
        self.sp = sp
        self.tp = tp

    def totale(self):
        return self.pp + self.sp + self.tp

    def __str__(self):
        return "PP: %s\nSP: %s\nTP: %s\n=========\nTOT: %s" % \
            (self.pp, self.sp, self.mp, self.mg, self.totale())


def partition(d1, d2):
    date = (d1.data, d2.data)
    diff_gas_generale = d2.gas_generale - d1.gas_generale

    if diff_gas_generale == 0:
        return Ripartizione(date, 0,0,0,0)

    diff_gas_pp = d2.gas_pp - d1.gas_pp
    diff_gas_sp = d2.gas_sp - d1.gas_sp
    diff_gas_tp = d2.gas_tp - d1.gas_tp

    euro_per_mc = d2.costo_bolletta / diff_gas_generale
    gas_h2o_calda = diff_gas_generale - diff_gas_tp - diff_gas_sp - diff_gas_pp
    costo_h2o_calda = euro_per_mc * gas_h2o_calda

    diff_calorie_pp_zona_giorno = d2.calorie_pp_zona_giorno - d1.calorie_pp_zona_giorno
    diff_calorie_pp_zona_notte = d2.calorie_pp_zona_notte - d1.calorie_pp_zona_notte
    diff_calorie_pp = diff_calorie_pp_zona_giorno + diff_calorie_pp_zona_notte
    diff_calorie_sp = d2.calorie_sp - d1.calorie_sp
    diff_calorie_tc = d2.calorie_tc - d1.calorie_tc
    diff_calorie_tp = d2.calorie_tp - d1.calorie_tp

    totale_calorie_riscaldamento = diff_calorie_pp + diff_calorie_sp + diff_calorie_tc + diff_calorie_tp
    diff_calorie_h2o_calda = d2.calorie_h2o_calda - d1.calorie_h2o_calda

    consumo_h2o_pp = (d2.h2o_calda_andata_pp - d1.h2o_calda_andata_pp) - (d2.h2o_calda_ricircolo_pp - d1.h2o_calda_ricircolo_pp)
    consumo_h2o_sp = (d2.h2o_calda_andata_sp - d1.h2o_calda_andata_sp) - (d2.h2o_calda_ricircolo_sp - d1.h2o_calda_ricircolo_sp)
    consumo_h2o_tp = (d2.h2o_calda_andata_tp - d1.h2o_calda_andata_tp) - (d2.h2o_calda_ricircolo_tp - d1.h2o_calda_ricircolo_tp)
    consumo_totale_h2o = consumo_h2o_pp + consumo_h2o_sp + consumo_h2o_tp

    ripartizione_pp = diff_calorie_pp + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_pp
    ripartizione_sp = diff_calorie_sp + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_sp
    ripartizione_tp = (diff_calorie_tc + diff_calorie_tp) + (diff_calorie_h2o_calda / consumo_totale_h2o) * consumo_h2o_tp

    res = Ripartizione()
    res.date = date
    res.pp = euro_per_mc * diff_gas_pp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_pp
    res.sp = euro_per_mc * diff_gas_sp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_sp
    res.tp = euro_per_mc * diff_gas_tp + costo_h2o_calda / (totale_calorie_riscaldamento + diff_calorie_h2o_calda) * ripartizione_tp

    return res
