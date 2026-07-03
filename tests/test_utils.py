from simplecron import utils
import pytest
import datetime


def test_weekdays():
    cases = [
        {
            'value': 'monday',
            'expected': 0,
            'is_exception': False
        },
        {
            'value': 'sunday',
            'expected': 6,
            'is_exception': False
        },
        {
            'value': 'invalid_day',
            'expected': None,
            'is_exception': True
        }
    ]

    for item in cases:
        if item['is_exception']:
            with pytest.raises(ValueError):
                utils.weekdays(item['value'])
        else:
            assert utils.weekdays(item['value']) == item['expected']


def test_move_to_next_weekday():
    cases = [
        {
            'dt': datetime.datetime(2024, 6, 10),  # Monday
            'target_weekday': 'wednesday',
            'expected': datetime.datetime(2024, 6, 12)  # Wednesday
        },
        {
            'dt': datetime.datetime(2024, 6, 10),  # Monday
            'target_weekday': 'monday',
            'expected': datetime.datetime(2024, 6, 17)  # Next Monday
        },
        {
            'dt': datetime.datetime(2024, 6, 10),  # Monday
            'target_weekday': 'sunday',
            'expected': datetime.datetime(2024, 6, 16)  # Sunday
        }
    ]

    for item in cases:
        assert utils.move_to_next_weekday(
            item['dt'],
            item['target_weekday']
        ) == item['expected']
