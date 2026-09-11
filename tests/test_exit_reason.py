import unittest

from backend.domain.journal import assess_exit


class ExitReasonTests(unittest.TestCase):
    def assess(self, **changes):
        return assess_exit(dict(status='closed', direction='long', planned_stop='95', planned_take='110', exit_prices=[100]) | changes)

    def test_long_and_short_levels_and_slippage(self):
        for direction, stop, take, prices, expected in (
            ('long', '95', '110', [95, 94.5], 'stop'),
            ('long', '95', '110', [110, 111], 'take'),
            ('long', '95', '110', [100, 103], 'manual'),
            ('short', '110', '95', [110, 111], 'stop'),
            ('short', '110', '95', [95, 94.5], 'take'),
            ('short', '110', '95', [100, 103], 'manual'),
        ):
            with self.subTest(direction=direction, prices=prices):
                result = self.assess(direction=direction, planned_stop=stop, planned_take=take, exit_prices=prices)
                self.assertEqual(result['reason'], expected)
                self.assertTrue(result['inferred'])

    def test_mixed_fills_not_average(self):
        self.assertEqual(self.assess(exit_prices=[94, 111])['reason'], 'mixed')

    def test_manual_default_without_both_levels(self):
        result = self.assess(planned_take='')
        self.assertEqual(result['reason'], 'manual')
        self.assertEqual(result['label'], 'Вышел руками')
        self.assertEqual(result['source'], 'default_rule')
        self.assertEqual(self.assess(planned_stop='')['reason'], 'manual')
        self.assertEqual(self.assess(planned_stop='', planned_take='')['reason'], 'manual')
        self.assertEqual(self.assess(planned_take='', exit_prices=[94])['reason'], 'stop')

    def test_open_invalid_or_missing_data(self):
        self.assertEqual(self.assess(status='open', exit_prices=[94])['reason'], 'open')
        for changes in ({'planned_stop': '120'}, {'exit_prices': []}, {'exit_prices': [None]}, {'planned_stop': 'NaN', 'planned_take': 'abc'}):
            with self.subTest(changes=changes):
                self.assertEqual(self.assess(**changes)['reason'], 'manual')

    def test_decimal_comma(self):
        self.assertEqual(self.assess(planned_stop='95,5', exit_prices=[95.5])['reason'], 'stop')

    def test_short_stop_with_grouping_spaces_and_no_take(self):
        for separator in (' ', '\u00a0', '\u202f'):
            with self.subTest(separator=repr(separator)):
                result = self.assess(direction='short', planned_stop=f'214{separator}550',
                                     planned_take='', exit_prices=[214563])
                self.assertEqual(result['reason'], 'stop')
                self.assertEqual(result['source'], 'plan_prices')

    def test_grouped_decimal_take(self):
        result = self.assess(direction='short', planned_stop='',
                             planned_take='210 500,5', exit_prices=[210500.5])
        self.assertEqual(result['reason'], 'take')


if __name__ == '__main__':
    unittest.main()
