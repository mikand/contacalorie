from sqlalchemy import create_engine, Column, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Datum(Base):
    __tablename__ = 'data'

    id = Column(String, primary_key=True)  # Assuming data is unique, or use an auto id
    data = Column(Date)
    gas_generale = Column(Float)
    gas_pp = Column(Float)
    gas_sp = Column(Float)
    gas_tp = Column(Float)
    calorie_pp_zona_giorno = Column(Float)
    calorie_pp_zona_notte = Column(Float)
    calorie_sp = Column(Float)
    calorie_tc = Column(Float)
    calorie_tp = Column(Float)
    calorie_h2o_calda = Column(Float)
    h2o_calda_andata_pp = Column(Float)
    h2o_calda_ricircolo_pp = Column(Float)
    h2o_calda_andata_sp = Column(Float)
    h2o_calda_ricircolo_sp = Column(Float)
    h2o_calda_andata_tp = Column(Float)
    h2o_calda_ricircolo_tp = Column(Float)
    costo_bolletta = Column(Float)

engine = create_engine('sqlite:///contacalorie.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def populate_from_sheets():
    import os.path
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(os.path.dirname(__file__), 'Contacalorie-cef2fe8fdd6c.json'), scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    sheet = client.open("DBContacalorieMaiano").sheet1

    # Extract all records
    list_of_hashes = sheet.get_all_records()

    session = Session()
    for d in list_of_hashes:
        datum = Datum(
            id=d['Data di rilevamento'],  # Assuming data is unique
            data=datetime.datetime.strptime(d['Data di rilevamento'], '%m/%d/%Y').date(),
            gas_generale=d['Contatore gas generale'],
            gas_pp=d['Contatore gas primo piano'],
            gas_sp=d['Contatore gas secondo piano'],
            gas_tp=d['Contatore gas terzo piano'],
            calorie_pp_zona_giorno=d['Contatore calorie primo piano zona giorno'],
            calorie_pp_zona_notte=d['Contatore calorie primo piano zona notte'],
            calorie_sp=d['Contatore calorie secondo piano'],
            calorie_tc=d['Contatore calorie taverna carlo'],
            calorie_tp=d['Contatore calorie terzo piano'],
            calorie_h2o_calda=d['Contatore calorie acqua calda'],
            h2o_calda_andata_pp=d['Contatore H2O calda andata primo piano'],
            h2o_calda_ricircolo_pp=d['Contatore H2O ricircolo primo piano'],
            h2o_calda_andata_sp=d['Contatore H2O calda andata secondo piano'],
            h2o_calda_ricircolo_sp=d['Contatore H2O ricircolo secondo piano'],
            h2o_calda_andata_tp=d['Contatore H2O calda andata terzo piano'],
            h2o_calda_ricircolo_tp=d['Contatore H2O ricircolo terzo piano'],
            costo_bolletta=d['Costo totale bolletta gas']
        )
        session.add(datum)
    session.commit()
    session.close()
    print("Data populated from Google Sheets.")

def get_data():
    session = Session()
    data = session.query(Datum).order_by(Datum.data).all()
    session.close()
    return data

def format_date_italian(date_obj):
    """Format date object as day/month/year (Italian style)"""
    if date_obj is None:
        return ""
    return date_obj.strftime('%d/%m/%Y')

class Ripartizione(object):
    def __init__(self, date=None, pp=None, sp=None, tp=None, error=None):
        self.date = date
        self.pp = pp
        self.sp = sp
        self.tp = tp
        self.error = error

    def is_error(self):
        return self.error is not None

    def totale(self):
        return self.pp + self.sp + self.tp

    def __str__(self):
        return "PP: %s\nSP: %s\nTP: %s\n=========\nTOT: %s" % \
            (self.pp, self.sp, self.tp, self.totale())


def partition(d1, d2) -> Ripartizione:
    date = (format_date_italian(d1.data), format_date_italian(d2.data))
    try:
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
    except Exception as e:
        res = Ripartizione()
        res.date = date
        res.error = str(e)
        return res
