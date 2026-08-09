import datetime

from sqlalchemy import create_engine, Column, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Reading(Base):
    __tablename__ = 'readings'

    # The date IS the record: one set of readings per day, uniqueness enforced
    # by the database instead of by application checks.
    date = Column(Date, primary_key=True)
    gas_main = Column(Float)
    gas_floor_1 = Column(Float)
    gas_floor_2 = Column(Float)
    gas_floor_3 = Column(Float)
    calories_floor_1_day_zone = Column(Float)
    calories_floor_1_night_zone = Column(Float)
    calories_floor_2 = Column(Float)
    calories_basement = Column(Float)
    calories_floor_3 = Column(Float)
    calories_hot_water = Column(Float)
    hot_water_supply_floor_1 = Column(Float)
    hot_water_return_floor_1 = Column(Float)
    hot_water_supply_floor_2 = Column(Float)
    hot_water_return_floor_2 = Column(Float)
    hot_water_supply_floor_3 = Column(Float)
    hot_water_return_floor_3 = Column(Float)
    bill_cost = Column(Float)

# Every meter except the date, in column order. Adding a meter means adding a
# column above and a label below; nothing else in the app lists the fields.
FIELDS = [c.name for c in Reading.__table__.columns if c.name != 'date']

# Identifiers are English, everything the resident reads is Italian: these
# labels are the only names for the meters that ever reach the browser.
LABELS = {
    'gas_main': 'Gas Generale',
    'gas_floor_1': 'Gas Primo Piano',
    'gas_floor_2': 'Gas Secondo Piano',
    'gas_floor_3': 'Gas Terzo Piano',
    'calories_floor_1_day_zone': 'Calorie Primo Piano Zona Giorno',
    'calories_floor_1_night_zone': 'Calorie Primo Piano Zona Notte',
    'calories_floor_2': 'Calorie Secondo Piano',
    'calories_basement': 'Calorie Taverna Carlo',
    'calories_floor_3': 'Calorie Terzo Piano',
    'calories_hot_water': 'Calorie H2O Calda',
    'hot_water_supply_floor_1': 'H2O Andata Primo Piano',
    'hot_water_return_floor_1': 'H2O Ricircolo Primo Piano',
    'hot_water_supply_floor_2': 'H2O Andata Secondo Piano',
    'hot_water_return_floor_2': 'H2O Ricircolo Secondo Piano',
    'hot_water_supply_floor_3': 'H2O Andata Terzo Piano',
    'hot_water_return_floor_3': 'H2O Ricircolo Terzo Piano',
    'bill_cost': 'Costo Bolletta',
}

# The form is grouped the way the meters are walked, and the field prefix is
# the group. A new meter joins its group by name alone; one with an unknown
# prefix lands in a trailing "Altro" rather than vanishing from the form.
FIELD_GROUPS = [('Gas', 'gas_'), ('Calorie', 'calories_'),
                ('Acqua Calda', 'hot_water_'), ('Bolletta', 'bill_')]

def grouped_fields():
    """FIELDS as a list of (group name, fields), in FIELD_GROUPS order."""
    groups = [(name, [f for f in FIELDS if f.startswith(prefix)])
              for name, prefix in FIELD_GROUPS]
    grouped = {f for _, fields in groups for f in fields}
    other = [f for f in FIELDS if f not in grouped]
    return [g for g in groups if g[1]] + ([('Altro', other)] if other else [])

# The Sheet's own column headings, which are Italian and not ours to rename.
SHEET_COLUMNS = {
    'gas_main': 'Contatore gas generale',
    'gas_floor_1': 'Contatore gas primo piano',
    'gas_floor_2': 'Contatore gas secondo piano',
    'gas_floor_3': 'Contatore gas terzo piano',
    'calories_floor_1_day_zone': 'Contatore calorie primo piano zona giorno',
    'calories_floor_1_night_zone': 'Contatore calorie primo piano zona notte',
    'calories_floor_2': 'Contatore calorie secondo piano',
    'calories_basement': 'Contatore calorie taverna carlo',
    'calories_floor_3': 'Contatore calorie terzo piano',
    'calories_hot_water': 'Contatore calorie acqua calda',
    'hot_water_supply_floor_1': 'Contatore H2O calda andata primo piano',
    'hot_water_return_floor_1': 'Contatore H2O ricircolo primo piano',
    'hot_water_supply_floor_2': 'Contatore H2O calda andata secondo piano',
    'hot_water_return_floor_2': 'Contatore H2O ricircolo secondo piano',
    'hot_water_supply_floor_3': 'Contatore H2O calda andata terzo piano',
    'hot_water_return_floor_3': 'Contatore H2O ricircolo terzo piano',
    'bill_cost': 'Costo totale bolletta gas',
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
        for row in sheet.get_all_records():
            reading = Reading(date=datetime.datetime.strptime(row['Data di rilevamento'], '%m/%d/%Y').date())
            for field, column in SHEET_COLUMNS.items():
                setattr(reading, field, float(row[column]))
            session.merge(reading)  # upsert by date, so re-running is harmless
        session.commit()
    print("Data populated from Google Sheets.")

def get_readings():
    with Session() as session:
        return session.query(Reading).order_by(Reading.date).all()

def format_date_italian(date_obj):
    """Format date object as day/month/year (Italian style)"""
    if date_obj is None:
        return ""
    return date_obj.strftime('%d/%m/%Y')

class CostSplit(object):
    def __init__(self, period=None, floor_1=None, floor_2=None, floor_3=None, error=None):
        self.period = period  # (date, date) — start and end of the period
        self.floor_1 = floor_1
        self.floor_2 = floor_2
        self.floor_3 = floor_3
        self.error = error
        # Every intermediate the help dialog shows, so the explanation is
        # generated by the same code that generates the bill and cannot drift
        # from it. None when there was nothing to compute (error, or no gas).
        self.steps = None

    def is_error(self):
        return self.error is not None

    def total(self):
        return self.floor_1 + self.floor_2 + self.floor_3

    def __str__(self):
        return "Floor 1: %s\nFloor 2: %s\nFloor 3: %s\n=========\nTOT: %s" % \
            (self.floor_1, self.floor_2, self.floor_3, self.total())


def split_costs(r1, r2) -> CostSplit:
    """Split the bill between the three apartments over the period r1..r2.

    The basement is billed together with floor 3; it has no share of its own.
    """
    period = (r1.date, r2.date)
    try:
        diff_gas_main = r2.gas_main - r1.gas_main

        if diff_gas_main == 0:
            return CostSplit(period, 0, 0, 0)

        diff_gas_floor_1 = r2.gas_floor_1 - r1.gas_floor_1
        diff_gas_floor_2 = r2.gas_floor_2 - r1.gas_floor_2
        diff_gas_floor_3 = r2.gas_floor_3 - r1.gas_floor_3

        euro_per_m3 = r2.bill_cost / diff_gas_main
        # What the central boiler burned: the main meter minus what each
        # apartment burned on its own sub-meter. It pays for the heating AND
        # the domestic hot water, which is why the calorie shares below weigh
        # both — "common", not "hot water".
        gas_common = diff_gas_main - diff_gas_floor_3 - diff_gas_floor_2 - diff_gas_floor_1
        cost_common = euro_per_m3 * gas_common

        diff_calories_floor_1_day_zone = r2.calories_floor_1_day_zone - r1.calories_floor_1_day_zone
        diff_calories_floor_1_night_zone = r2.calories_floor_1_night_zone - r1.calories_floor_1_night_zone
        diff_calories_floor_1 = diff_calories_floor_1_day_zone + diff_calories_floor_1_night_zone
        diff_calories_floor_2 = r2.calories_floor_2 - r1.calories_floor_2
        diff_calories_basement = r2.calories_basement - r1.calories_basement
        diff_calories_floor_3 = r2.calories_floor_3 - r1.calories_floor_3

        total_heating_calories = diff_calories_floor_1 + diff_calories_floor_2 + diff_calories_basement + diff_calories_floor_3
        diff_calories_hot_water = r2.calories_hot_water - r1.calories_hot_water

        water_use_floor_1 = (r2.hot_water_supply_floor_1 - r1.hot_water_supply_floor_1) - (r2.hot_water_return_floor_1 - r1.hot_water_return_floor_1)
        water_use_floor_2 = (r2.hot_water_supply_floor_2 - r1.hot_water_supply_floor_2) - (r2.hot_water_return_floor_2 - r1.hot_water_return_floor_2)
        water_use_floor_3 = (r2.hot_water_supply_floor_3 - r1.hot_water_supply_floor_3) - (r2.hot_water_return_floor_3 - r1.hot_water_return_floor_3)
        total_water_use = water_use_floor_1 + water_use_floor_2 + water_use_floor_3

        # Each floor's weight in the common cost: its own heating calories,
        # plus its cut of the central hot-water calorie meter, handed out in
        # proportion to the net water it actually drew.
        # The three shares add up to shares_total by construction, so the
        # split always closes on the bill.
        shares_total = total_heating_calories + diff_calories_hot_water
        floors = {
            'floor_1': (diff_gas_floor_1, diff_calories_floor_1, water_use_floor_1),
            'floor_2': (diff_gas_floor_2, diff_calories_floor_2, water_use_floor_2),
            # The basement has no share of its own: it is billed with floor 3.
            'floor_3': (diff_gas_floor_3, diff_calories_floor_3 + diff_calories_basement, water_use_floor_3),
        }

        split = CostSplit(period)
        split.steps = {
            'bill_cost': r2.bill_cost,
            # The two raw readings behind one delta, so the help dialog can
            # show what "delta" means on a concrete meter.
            'gas_main_start': r1.gas_main,
            'gas_main_end': r2.gas_main,
            'diff_gas_main': diff_gas_main,
            'euro_per_m3': euro_per_m3,
            'gas_common': gas_common,
            'cost_common': cost_common,
            'diff_calories_hot_water': diff_calories_hot_water,
            'total_heating_calories': total_heating_calories,
            'total_water_use': total_water_use,
            'shares_total': shares_total,
        }
        for name, (diff_gas, diff_calories, water_use) in floors.items():
            hot_water_calories = diff_calories_hot_water / total_water_use * water_use
            share = diff_calories + hot_water_calories
            gas_cost = euro_per_m3 * diff_gas
            common_cost = cost_common / shares_total * share
            split.steps[name] = {
                'diff_gas': diff_gas,
                'diff_calories': diff_calories,
                'water_use': water_use,
                'hot_water_calories': hot_water_calories,
                'share': share,
                'gas_cost': gas_cost,
                'common_cost': common_cost,
                'total': gas_cost + common_cost,
            }
            setattr(split, name, gas_cost + common_cost)

        # Floor 3's share lumps the basement in. The diagram draws them as the
        # two separate meters they are, so keep both figures as well as the sum.
        split.steps['floor_3']['diff_calories_own'] = diff_calories_floor_3
        split.steps['floor_3']['diff_calories_basement'] = diff_calories_basement

        return split
    except Exception as e:
        split = CostSplit()
        split.period = period
        split.error = str(e)
        return split
