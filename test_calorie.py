#!/usr/bin/env python
"""Checks on the money math. Run: python test_calorie.py"""

import datetime

from calorie import Reading, split_costs

# Two real consecutive readings (bill 93.05 EUR). In this period no
# apartment burned its own gas, so the whole bill is split through the
# hot-water/heating calorie shares.
JANUARY = Reading(
    date=datetime.date(2026, 1, 31),
    gas_main=3638.0, gas_floor_1=139.0, gas_floor_2=347.0, gas_floor_3=191.0,
    calories_floor_1_day_zone=7038.0, calories_floor_1_night_zone=5648.0,
    calories_floor_2=17790.0, calories_basement=8991.0, calories_floor_3=1.0,
    calories_hot_water=22331.0,
    hot_water_supply_floor_1=59.0, hot_water_return_floor_1=0.0,
    hot_water_supply_floor_2=503.0, hot_water_return_floor_2=0.0,
    hot_water_supply_floor_3=64.1, hot_water_return_floor_3=1.0,
    bill_cost=122.9,
)

FEBRUARY = Reading(
    date=datetime.date(2026, 2, 28),
    gas_main=3715.0, gas_floor_1=139.0, gas_floor_2=347.0, gas_floor_3=191.0,
    calories_floor_1_day_zone=7040.0, calories_floor_1_night_zone=5688.0,
    calories_floor_2=17790.0, calories_basement=9458.0, calories_floor_3=1.0,
    calories_hot_water=22421.0,
    hot_water_supply_floor_1=60.0, hot_water_return_floor_1=0.0,
    hot_water_supply_floor_2=503.0, hot_water_return_floor_2=0.0,
    hot_water_supply_floor_3=64.2, hot_water_return_floor_3=1.0,
    bill_cost=93.05,
)


def test_preserves_the_total():
    """The three shares must add up to the bill exactly — no money invented
    or lost. This is the invariant that must survive any refactoring."""
    s = split_costs(JANUARY, FEBRUARY)
    assert not s.is_error(), s.error
    assert abs(s.total() - FEBRUARY.bill_cost) < 0.005, s.total()


def test_known_values():
    """Regression: the figures this period has always produced."""
    s = split_costs(JANUARY, FEBRUARY)
    assert round(s.floor_1, 2) == 19.23, s.floor_1
    assert round(s.floor_2, 2) == 0.00, s.floor_2
    assert round(s.floor_3, 2) == 73.82, s.floor_3


def test_period_with_zero_gas():
    """No gas burned means nobody pays — and that is NOT an error.
    Regression for CostSplit(period, 0, 0, 0, 0), which used to pass the
    fourth zero as `error` and render the period as a failure."""
    s = split_costs(JANUARY, JANUARY)
    assert not s.is_error(), s.error
    assert s.total() == 0


def test_no_water_use_is_an_error():
    """Gas burned but no hot water drawn anywhere divides by zero. It must
    come back as an error object, not blow up the page."""
    no_water = Reading(**{c.name: getattr(JANUARY, c.name)
                          for c in Reading.__table__.columns})
    no_water.date = datetime.date(2026, 2, 28)
    no_water.gas_main = JANUARY.gas_main + 10
    s = split_costs(JANUARY, no_water)
    assert s.is_error()
    assert s.period == (JANUARY.date, no_water.date)


def test_steps_reproduce_the_split():
    """The help dialog only prints `steps`, so every number it shows must
    reconcile with the money actually billed. If this fails, the explanation
    on screen is lying about the bill next to it."""
    s = split_costs(JANUARY, FEBRUARY)
    steps = s.steps
    for floor in ('floor_1', 'floor_2', 'floor_3'):
        part = steps[floor]
        assert abs(part['gas_cost'] + part['common_cost'] - part['total']) < 1e-9, floor
        assert abs(part['total'] - getattr(s, floor)) < 1e-9, floor
    # The shares are a partition of the divisor, which is what makes the
    # common cost close on itself rather than leaking money.
    shares = sum(steps[f]['share'] for f in ('floor_1', 'floor_2', 'floor_3'))
    assert abs(shares - steps['shares_total']) < 1e-6, shares
    assert abs(steps['euro_per_m3'] * steps['gas_common'] - steps['cost_common']) < 1e-9


def test_no_steps_when_there_is_nothing_to_explain():
    """The dialog shows dashes rather than invented numbers, so `steps` must
    be absent exactly when the period produced no calculation."""
    assert split_costs(JANUARY, JANUARY).steps is None   # no gas burned
    no_water = Reading(**{c.name: getattr(JANUARY, c.name)
                          for c in Reading.__table__.columns})
    no_water.date = datetime.date(2026, 2, 28)
    no_water.gas_main = JANUARY.gas_main + 10
    assert split_costs(JANUARY, no_water).steps is None   # divides by zero


def test_help_dialog_asks_for_keys_that_exist():
    """Every data-v in the help dialog is looked up in `steps` at runtime; a
    typo would silently render as an em dash forever instead of failing."""
    import re
    from flask import render_template
    from calorie import FIELDS, LABELS, grouped_fields
    from website import app

    with app.app_context():
        html = render_template('index.html', fields=FIELDS, groups=grouped_fields(),
                               labels=LABELS, copyright_date=2026)

    steps = split_costs(JANUARY, FEBRUARY).steps
    for path in sorted(set(re.findall(r'data-v="([^"]+)"', html))):
        node = steps
        for key in path.split('.'):
            node = node.get(key) if isinstance(node, dict) else None
        assert isinstance(node, float), path


def test_period_holds_date_objects():
    """The API and the report both format the period themselves, so
    split_costs must hand back real dates rather than pre-formatted strings."""
    s = split_costs(JANUARY, FEBRUARY)
    assert s.period == (datetime.date(2026, 1, 31), datetime.date(2026, 2, 28))


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
    print('all tests passed')
