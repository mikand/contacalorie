import datetime

from sqlalchemy import create_engine, Column, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Datum(Base):
    __tablename__ = 'data'

    # The date IS the record: one set of readings per day, uniqueness enforced
    # by the database instead of by application checks.
    data = Column(Date, primary_key=True)
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

# Every meter except the date, in column order. Adding a meter means adding a
# column above and a label below; nothing else in the app lists the fields.
FIELDS = [c.name for c in Datum.__table__.columns if c.name != 'data']

LABELS = {
    'gas_generale': 'Gas Generale',
    'gas_pp': 'Gas Primo Piano',
    'gas_sp': 'Gas Secondo Piano',
    'gas_tp': 'Gas Terzo Piano',
    'calorie_pp_zona_giorno': 'Calorie Primo Piano Zona Giorno',
    'calorie_pp_zona_notte': 'Calorie Primo Piano Zona Notte',
    'calorie_sp': 'Calorie Secondo Piano',
    'calorie_tc': 'Calorie Taverna Carlo',
    'calorie_tp': 'Calorie Terzo Piano',
    'calorie_h2o_calda': 'Calorie H2O Calda',
    'h2o_calda_andata_pp': 'H2O Andata Primo Piano',
    'h2o_calda_ricircolo_pp': 'H2O Ricircolo Primo Piano',
    'h2o_calda_andata_sp': 'H2O Andata Secondo Piano',
    'h2o_calda_ricircolo_sp': 'H2O Ricircolo Secondo Piano',
    'h2o_calda_andata_tp': 'H2O Andata Terzo Piano',
    'h2o_calda_ricircolo_tp': 'H2O Ricircolo Terzo Piano',
    'costo_bolletta': 'Costo Bolletta',
}

SHEET_COLUMNS = {
    'gas_generale': 'Contatore gas generale',
    'gas_pp': 'Contatore gas primo piano',
    'gas_sp': 'Contatore gas secondo piano',
    'gas_tp': 'Contatore gas terzo piano',
    'calorie_pp_zona_giorno': 'Contatore calorie primo piano zona giorno',
    'calorie_pp_zona_notte': 'Contatore calorie primo piano zona notte',
    'calorie_sp': 'Contatore calorie secondo piano',
    'calorie_tc': 'Contatore calorie taverna carlo',
    'calorie_tp': 'Contatore calorie terzo piano',
    'calorie_h2o_calda': 'Contatore calorie acqua calda',
    'h2o_calda_andata_pp': 'Contatore H2O calda andata primo piano',
    'h2o_calda_ricircolo_pp': 'Contatore H2O ricircolo primo piano',
    'h2o_calda_andata_sp': 'Contatore H2O calda andata secondo piano',
    'h2o_calda_ricircolo_sp': 'Contatore H2O ricircolo secondo piano',
    'h2o_calda_andata_tp': 'Contatore H2O calda andata terzo piano',
    'h2o_calda_ricircolo_tp': 'Contatore H2O ricircolo terzo piano',
    'costo_bolletta': 'Costo totale bolletta gas',
}

engine = create_engine('sqlite:///contacalorie.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def populate_from_sheets():
    """Import every row of the Google Sheet, overwriting same-date records.

    The Sheet was retired as the source of truth once the web UI took over;
    this stays as the recovery path back to the historical data.
    """
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

    with Session() as session:
        for d in sheet.get_all_records():
            datum = Datum(data=datetime.datetime.strptime(d['Data di rilevamento'], '%m/%d/%Y').date())
            for field, column in SHEET_COLUMNS.items():
                setattr(datum, field, float(d[column]))
            session.merge(datum)  # upsert by date, so re-running is harmless
        session.commit()
    print("Data populated from Google Sheets.")

def get_data():
    with Session() as session:
        return session.query(Datum).order_by(Datum.data).all()

def format_date_italian(date_obj):
    """Format date object as day/month/year (Italian style)"""
    if date_obj is None:
        return ""
    return date_obj.strftime('%d/%m/%Y')

class Ripartizione(object):
    def __init__(self, date=None, pp=None, sp=None, tp=None, error=None):
        self.date = date  # (date, date) — start and end of the period
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
    date = (d1.data, d2.data)
    try:
        diff_gas_generale = d2.gas_generale - d1.gas_generale

        if diff_gas_generale == 0:
            return Ripartizione(date, 0, 0, 0)

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
