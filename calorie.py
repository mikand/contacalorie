import os.path
import gspread

from oauth2client.service_account import ServiceAccountCredentials

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
    seen = set()
    for d in list_of_hashes:
        datum = Datum.from_dict(d)
        if datum not in seen:
            res.append(datum)
            seen.add(datum)
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

    def __hash__(self):
        return hash(self.data) + hash(self.gas_generale) + hash(self.gas_pp) + \
            hash(self.gas_sp) + hash(self.gas_mp) + hash(self.calorie_pp_zona_giorno) + \
            hash(self.calorie_pp_zona_notte) + hash(self.calorie_sp) + \
            hash(self.calorie_mp) + hash(self.calorie_mg) + \
            hash(self.calorie_h2o_calda) + hash(self.h2o_calda_andata_pp) + \
            hash(self.h2o_calda_ricircolo_pp) + hash(self.h2o_calda_andata_sp) + \
            hash(self.h2o_calda_ricircolo_sp) + hash(self.h2o_calda_andata_mp) + \
            hash(self.h2o_calda_ricircolo_mp) + hash(self.h2o_calda_andata_mg) + \
            hash(self.h2o_calda_ricircolo_mg) + hash(self.costo_bolletta)

    def __eq__(self, oth):
        if self.data != oth.data: return False
        if self.gas_generale != oth.gas_generale: return False
        if self.gas_pp != oth.gas_pp: return False
        if self.gas_sp != oth.gas_sp: return False
        if self.gas_mp != oth.gas_mp: return False
        if self.calorie_pp_zona_giorno != oth.calorie_pp_zona_giorno: return False
        if self.calorie_pp_zona_notte != oth.calorie_pp_zona_notte: return False
        if self.calorie_sp != oth.calorie_sp: return False
        if self.calorie_mp != oth.calorie_mp: return False
        if self.calorie_mg != oth.calorie_mg: return False
        if self.calorie_h2o_calda != oth.calorie_h2o_calda: return False
        if self.h2o_calda_andata_pp != oth.h2o_calda_andata_pp: return False
        if self.h2o_calda_ricircolo_pp != oth.h2o_calda_ricircolo_pp: return False
        if self.h2o_calda_andata_sp != oth.h2o_calda_andata_sp: return False
        if self.h2o_calda_ricircolo_sp != oth.h2o_calda_ricircolo_sp: return False
        if self.h2o_calda_andata_mp != oth.h2o_calda_andata_mp: return False
        if self.h2o_calda_ricircolo_mp != oth.h2o_calda_ricircolo_mp: return False
        if self.h2o_calda_andata_mg != oth.h2o_calda_andata_mg: return False
        if self.h2o_calda_ricircolo_mg != oth.h2o_calda_ricircolo_mg: return False
        if self.costo_bolletta != oth.costo_bolletta: return False

        return True

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
