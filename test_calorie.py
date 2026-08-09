#!/usr/bin/env python
"""Checks on the money math. Run: python test_calorie.py"""

import datetime

from calorie import Datum, partition

# Two real consecutive readings (bolletta 93.05 EUR). In this period no
# apartment burned its own gas, so the whole bill is split through the
# hot-water/heating calorie shares.
GENNAIO = Datum(
    data=datetime.date(2026, 1, 31),
    gas_generale=3638.0, gas_pp=139.0, gas_sp=347.0, gas_tp=191.0,
    calorie_pp_zona_giorno=7038.0, calorie_pp_zona_notte=5648.0,
    calorie_sp=17790.0, calorie_tc=8991.0, calorie_tp=1.0,
    calorie_h2o_calda=22331.0,
    h2o_calda_andata_pp=59.0, h2o_calda_ricircolo_pp=0.0,
    h2o_calda_andata_sp=503.0, h2o_calda_ricircolo_sp=0.0,
    h2o_calda_andata_tp=64.1, h2o_calda_ricircolo_tp=1.0,
    costo_bolletta=122.9,
)

FEBBRAIO = Datum(
    data=datetime.date(2026, 2, 28),
    gas_generale=3715.0, gas_pp=139.0, gas_sp=347.0, gas_tp=191.0,
    calorie_pp_zona_giorno=7040.0, calorie_pp_zona_notte=5688.0,
    calorie_sp=17790.0, calorie_tc=9458.0, calorie_tp=1.0,
    calorie_h2o_calda=22421.0,
    h2o_calda_andata_pp=60.0, h2o_calda_ricircolo_pp=0.0,
    h2o_calda_andata_sp=503.0, h2o_calda_ricircolo_sp=0.0,
    h2o_calda_andata_tp=64.2, h2o_calda_ricircolo_tp=1.0,
    costo_bolletta=93.05,
)


def test_conserva_il_totale():
    """The three shares must add up to the bill exactly — no money invented
    or lost. This is the invariant that must survive any refactoring."""
    r = partition(GENNAIO, FEBBRAIO)
    assert not r.is_error(), r.error
    assert abs(r.totale() - FEBBRAIO.costo_bolletta) < 0.005, r.totale()


def test_valori_noti():
    """Regression: the figures this period has always produced."""
    r = partition(GENNAIO, FEBBRAIO)
    assert round(r.pp, 2) == 19.23, r.pp
    assert round(r.sp, 2) == 0.00, r.sp
    assert round(r.tp, 2) == 73.82, r.tp


def test_periodo_a_gas_zero():
    """No gas burned means nobody pays — and that is NOT an error.
    Regression for Ripartizione(date, 0, 0, 0, 0), which used to pass the
    fourth zero as `error` and render the period as a failure."""
    r = partition(GENNAIO, GENNAIO)
    assert not r.is_error(), r.error
    assert r.totale() == 0


def test_h2o_senza_consumo_e_un_errore():
    """Gas burned but no hot water drawn anywhere divides by zero. It must
    come back as an error object, not blow up the page."""
    fermo = Datum(**{c.name: getattr(GENNAIO, c.name)
                     for c in Datum.__table__.columns})
    fermo.data = datetime.date(2026, 2, 28)
    fermo.gas_generale = GENNAIO.gas_generale + 10
    r = partition(GENNAIO, fermo)
    assert r.is_error()
    assert r.date == (GENNAIO.data, fermo.data)


def test_date_sono_oggetti_date():
    """The API and the report both format the period themselves, so partition
    must hand back real dates rather than pre-formatted strings."""
    r = partition(GENNAIO, FEBBRAIO)
    assert r.date == (datetime.date(2026, 1, 31), datetime.date(2026, 2, 28))


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
    print('tutti i test passati')
