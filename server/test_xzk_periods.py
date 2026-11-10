"""小灶课 ID 保存和期别来源回归检查，不写入数据库。"""
import unittest
from unittest.mock import MagicMock, patch
import performance_configuration_server as app


class XzkPeriodTests(unittest.TestCase):
    def setUp(self):
        self.repo = app.PerformanceConfigurationRepository()
        self.repo.fetch_all = MagicMock(return_value=[
            {'id': 2147483647, 'period_name': '26秋10月小灶课-初中数学'},
            {'id': 2, 'period_name': '26春小灶课'},
        ])

    def test_ids_are_strings_and_periods_remain_independent(self):
        row = self.repo.normalize_configuration_row({
            'configMonth': '2099-11', 'module': '小灶课',
            'xzkPeriodId': ['2', '2147483647', '2'],
            'periods': ['2026秋'],
        }, None)
        self.assertEqual(row[10], ['2026秋'])
        self.assertEqual(row[8], '2026秋')
        self.assertEqual(row[11], ['2', '2147483647'])

    def test_exercise_xzk_keeps_periods_and_ids(self):
        row = self.repo.normalize_configuration_row({
            'configMonth': '2099-11', 'module': '刷题班小灶课',
            'periods': ['2026秋'], 'xzkPeriodId': ['2'],
        }, None)
        self.assertEqual(row[10], ['2026秋'])
        self.assertEqual(row[11], ['2'])
        self.assertEqual(self.repo.period_options('刷题班小灶课')[0]['id'], '2147483647')

    def test_invalid_or_deleted_id_is_rejected(self):
        for value in ['abc', '1.2', '2147483648', '99']:
            with self.assertRaises(ValueError):
                self.repo.normalize_configuration_row({
                    'configMonth': '2099-11', 'module': '小灶课', 'xzkPeriodId': [value],
                }, None)

    def test_options_keep_id_and_sort_by_id(self):
        options = self.repo.period_options('小灶课')
        self.assertEqual(options[0]['id'], '2147483647')
        self.assertIn('ORDER BY id DESC', self.repo.fetch_all.call_args.args[0])

    def test_save_templates_match_values_with_or_without_sort_column(self):
        self.repo.with_connection = MagicMock()
        for has_sort in [True, False]:
            self.repo.has_sort_order_column = MagicMock(return_value=has_sort)
            with patch.object(app, 'execute_values') as execute:
                self.repo.batch_upsert({'rows': [{
                    'configMonth': '2099-11', 'module': '小灶课', 'xzkPeriodId': ['2'],
                }]}, None)
                args, kwargs = execute.call_args
                self.assertEqual(kwargs['template'].count('%s'), len(args[2][0]))
                self.assertIn('xzk_period_id = EXCLUDED.xzk_period_id', args[1])
                self.assertEqual(args[2][0][11], ['2'])
                self.assertIn('%s::integer[]', kwargs['template'])


if __name__ == '__main__':
    unittest.main()
