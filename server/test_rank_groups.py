"""Database-free regression checks for dynamic renewal rank groups."""
import unittest
from unittest.mock import MagicMock

from performance_configuration_server import (
    PerformanceConfigurationRepository, parse_renewal_target_import_rows,
)


class RankGroupTests(unittest.TestCase):
    def setUp(self):
        self.repo = PerformanceConfigurationRepository.__new__(PerformanceConfigurationRepository)
        self.repo.qualified_rank_group_table = 'bi.dim_renewal_rank_group'
        self.options = [{'id': '123', 'groupName': '七八年级创新'}]

    def test_import_resolves_names_and_ids_and_reports_missing_groups(self):
        for header in ['排名分组', 'renewalRankGroupId', 'renewal_rank_group_id', 'renewalRankGroup', 'renewal_rank_group']:
            result = parse_renewal_target_import_rows([
                ['年级', '班型', header], ['7', '创新', '七八年级创新'],
                ['8', '创新', '123'], ['9', '创新', '不存在'],
            ], [107], [], self.options)
            self.assertEqual([r['renewalRankGroupId'] for r in result['records']], [123, 123])
            self.assertEqual(len(result['errors']), 1)
            self.assertIn('不存在', result['errors'][0])

    def test_normalization_requires_id_and_retains_large_ids(self):
        row = {'renewalPeriodId': 107, 'grade': 7}
        self.assertIsNone(self.repo.normalize_renewal_target_row(row)['values'][-1])
        self.assertEqual(self.repo.normalize_renewal_target_row(dict(row, renewalRankGroupId='9223372036854775807'))['values'][-1], 9223372036854775807)
        with self.assertRaisesRegex(ValueError, '分组ID'):
            self.repo.normalize_renewal_target_row(dict(row, renewalRankGroupId='七八年级创新'))

    def test_existing_group_is_reused_without_inserting(self):
        self.repo.fetch_all = MagicMock(return_value=[{'id': 123}])
        self.repo.with_connection = MagicMock()
        self.assertEqual(self.repo.create_rank_group({'groupName': ' 七八年级创新 '}), self.options[0])
        self.repo.with_connection.assert_not_called()

    def test_create_persists_and_repeated_requests_use_same_id(self):
        self.repo.fetch_all = MagicMock(return_value=[])
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('新分组',)
        self.repo.with_connection = MagicMock()
        self.repo.with_connection.return_value.__enter__.return_value = connection
        a = self.repo.create_rank_group({'groupName': '新分组'})
        b = self.repo.create_rank_group({'groupName': '新分组'})
        self.assertEqual(a, b)
        self.assertTrue(a['id'].isdigit())
        self.assertIn('INSERT INTO bi.dim_renewal_rank_group', cursor.execute.call_args_list[0].args[0])
        self.assertEqual(connection.commit.call_count, 2)
        for name in ['', '  ', 'x' * 129]:
            with self.assertRaises(ValueError):
                self.repo.create_rank_group({'groupName': name})

    def test_invalid_reference_prevents_target_writes(self):
        self.repo.rank_group_options = MagicMock(return_value=self.options)
        self.repo.with_connection = MagicMock()
        with self.assertRaisesRegex(ValueError, '排名分组不存在'):
            self.repo.batch_upsert_renewal_targets({'rows': [{'renewalPeriodId': 107, 'grade': 7, 'renewalRankGroupId': 456}]})
        self.repo.with_connection.assert_not_called()

    def test_target_write_sql_binds_group_id_for_update_and_insert(self):
        self.repo.renewal_target_table = 'bi_renewal_target_rate'
        self.repo.qualified_renewal_target_table = 'bi.bi_renewal_target_rate'
        self.repo.rank_group_options = MagicMock(return_value=self.options)
        self.repo.has_sort_order_column = MagicMock(return_value=True)
        self.repo.has_period_group_key_column = MagicMock(return_value=True)
        self.repo.has_del_flag_column = MagicMock(return_value=True)
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.rowcount = 0
        self.repo.with_connection = MagicMock()
        self.repo.with_connection.return_value.__enter__.return_value = conn
        row = {'renewalPeriodId': 107, 'grade': 7, 'subject': 3, 'renewalRankGroupId': '123'}
        self.repo.batch_upsert_renewal_targets({'rows': [row, dict(row, delFlag=1)]})
        calls = cursor.execute.call_args_list
        self.assertEqual(len(calls), 3)
        for call in calls:
            sql, params = call.args
            self.assertEqual(sql.count('%s'), len(params))
        self.assertIn('renewal_rank_group_id = %s', calls[0].args[0])
        self.assertEqual(calls[0].args[1][11], 123)
        self.assertIn('INSERT INTO', calls[1].args[0])
        self.assertEqual(calls[1].args[1][11], 123)


if __name__ == '__main__':
    unittest.main()
