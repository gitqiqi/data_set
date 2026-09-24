#!/usr/bin/env python3
"""Small local backend for the performance configuration page."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sys
import time
import traceback
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlparse

try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2.pool import ThreadedConnectionPool
except ImportError:  # pragma: no cover - startup guard
    print("缺少 psycopg2，请先安装 psycopg2-binary。", file=sys.stderr)
    raise


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
ENV_FILE = PROJECT_ROOT / ".env"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PERFORMANCE_MODULE_KEY = "performance"
RENEWAL_TARGET_MODULE_KEY = "renewalTarget"
DUAL_PERIOD_MODULES = {"带生数", "刷题班带生数"}
CONFIG_TYPE_MODULES = {"带生数", "刷题班带生数"}
CONFIG_TYPE_VALUES = {"常规", "招生季"}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def require_identifier(value: str, fallback: str) -> str:
    text = (value or fallback).strip()
    if not IDENTIFIER_RE.match(text):
        raise ValueError(f"非法数据库标识符: {text}")
    return text


def parse_json_body(handler: BaseHTTPRequestHandler) -> Any:
    content_length = int(handler.headers.get("Content-Length") or 0)
    if content_length <= 0:
        return {}
    body = handler.rfile.read(content_length).decode("utf-8")
    return json.loads(body) if body else {}


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def normalize_month(value: Any) -> str:
    text = str(value or "").strip()
    match = re.match(r"^(\d{4})[-/年](\d{1,2})", text)
    if not match:
        return text
    return f"{match.group(1)}-{int(match.group(2)):02d}"


def current_config_month() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def is_historical_config_month(value: Any) -> bool:
    month = normalize_month(value)
    return bool(re.match(r"^\d{4}-\d{2}$", month)) and month < current_config_month()


def parse_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip().replace("/", "-")
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not match:
        raise ValueError(f"日期格式不正确: {value}")
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def parse_datetime(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def as_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not re.match(r"^-?\d+$", text):
        return None
    return int(text)


def renewal_period_group_ids(value: Any, fallback_period_id: Any = None) -> List[int]:
    items = value if isinstance(value, (list, tuple, set)) else re.split(r"\+", str(value or ""))
    ids: List[int] = []
    for item in items:
        period_id = as_int(item)
        if period_id is not None and period_id not in ids:
            ids.append(period_id)
    if not ids:
        fallback = as_int(fallback_period_id)
        if fallback is not None:
            ids.append(fallback)
    return sorted(ids, reverse=True)


def normalize_renewal_period_group_key(value: Any, fallback_period_id: Any = None) -> str:
    return "+".join(str(period_id) for period_id in renewal_period_group_ids(value, fallback_period_id))


def as_smallint(value: Any, default: int = 0) -> int:
    number = as_int(value)
    return default if number is None else number


def parse_decimal(value: Any) -> Optional[Decimal]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None

    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()

    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"数字格式不正确: {value}") from exc
    return number / Decimal("100") if is_percent else number


def first_value(row: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def request_module_key(payload: Any) -> str:
    if not isinstance(payload, dict):
        return PERFORMANCE_MODULE_KEY
    raw_value = first_value(
        payload,
        "moduleKey",
        "module_key",
        "configurationModule",
        "configuration_module",
        default=None,
    )
    if raw_value is None or not str(raw_value).strip():
        return PERFORMANCE_MODULE_KEY
    text = str(raw_value).strip()
    if text in {RENEWAL_TARGET_MODULE_KEY, "renewal_target", "renewal-target"}:
        return RENEWAL_TARGET_MODULE_KEY
    if text in {PERFORMANCE_MODULE_KEY, "performance_configuration", "performance-configuration"}:
        return PERFORMANCE_MODULE_KEY
    return text


def normalize_period_list(value: Any) -> List[str]:
    values = []
    items = value if isinstance(value, (list, tuple, set)) else [value]
    for item in items:
        for part in re.split(r"[,，、/]", str(item or "")):
            text = part.strip()
            if not text:
                continue
            text = re.sub(r"^(\d{2})(?=[\u4e00-\u9fa5])", r"20\1", text)
            values.append(text)
    return list(dict.fromkeys(values))


def is_dual_period_module(module: str) -> bool:
    return module.strip() in DUAL_PERIOD_MODULES


def normalize_period_fields(row: Dict[str, Any], module: str) -> Tuple[str, str, List[str]]:
    period1_values = normalize_period_list(first_value(row, "period1", "period_1", default=""))
    period2_values = normalize_period_list(first_value(row, "period2", "period_2", default=""))
    fallback_values = normalize_period_list(first_value(row, "periods", default=[]))

    if not is_dual_period_module(module):
        periods = normalize_period_list([*fallback_values, *period1_values])
        period1 = periods[0] if periods else ""
        return period1, "", periods

    period1 = period1_values[0] if period1_values else (fallback_values[0] if fallback_values else "")
    period2 = ""
    period2 = (
        period2_values[0]
        if period2_values
        else (period1_values[1] if len(period1_values) > 1 else "")
    )
    if not period2:
        period2 = next((period for period in fallback_values if period != period1), "")

    periods = normalize_period_list([period1, period2])
    return period1, period2, periods


def password_matches(input_password: str, stored_password: Any) -> bool:
    stored = str(stored_password or "").strip()
    if not stored:
        return False

    if hmac.compare_digest(stored, input_password):
        return True

    raw = input_password.encode("utf-8")
    candidates = {
        hashlib.md5(raw).hexdigest(),
        hashlib.sha256(raw).hexdigest(),
    }
    return any(hmac.compare_digest(stored.lower(), candidate.lower()) for candidate in candidates)


def sanitize_admin_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in row.items() if key != "password"}


def has_view_permission(rows: Iterable[Dict[str, Any]]) -> bool:
    return any(as_smallint(row.get("status"), 0) == 1 for row in rows)


def has_edit_permission(rows: Iterable[Dict[str, Any]]) -> bool:
    return any(
        as_smallint(row.get("status"), 0) == 1
        and as_smallint(row.get("permission_scope"), -1) == 2
        for row in rows
    )


def safe_next_path(value: str) -> str:
    text = value.strip() or "/performance-configuration.html"
    if not text.startswith("/") or text.startswith("//"):
        return "/performance-configuration.html"
    return text


def connection_kwargs() -> Dict[str, Any]:
    load_env_file(ENV_FILE)

    host = env("HOLO_HOST")
    port = env("HOLO_PORT", "80")
    database = env("HOLO_DATABASE")
    user = env("HOLO_USER")
    password = env("HOLO_PASSWORD")

    missing = [
        key for key, value in {
            "HOLO_HOST": host,
            "HOLO_PORT": port,
            "HOLO_DATABASE": database,
            "HOLO_USER": user,
            "HOLO_PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"缺少数据库配置: {', '.join(missing)}")

    return {
        "host": host,
        "port": int(port),
        "dbname": database,
        "user": user,
        "password": password,
        "sslmode": env("HOLO_SSLMODE", "prefer"),
        "connect_timeout": int(env("HOLO_CONNECT_TIMEOUT", "10")),
    }


class ConnectionContext:
    def __init__(self, pool: ThreadedConnectionPool) -> None:
        self.pool = pool
        self.conn = None

    def __enter__(self):
        self.conn = self.pool.getconn()
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is not None:
            if exc_type is not None:
                self.conn.rollback()
            self.pool.putconn(self.conn)


class PerformanceConfigurationRepository:
    def __init__(self) -> None:
        load_env_file(ENV_FILE)
        self.schema = require_identifier(env("HOLO_SCHEMA", "bi"), "bi")
        self.performance_table = require_identifier(env("HOLO_TABLE", "performance_configuration"), "performance_configuration")
        self.renewal_target_table = require_identifier(
            env("HOLO_RENEWAL_TARGET_TABLE", "bi_renewal_target_rate"),
            "bi_renewal_target_rate",
        )
        self.table = self.performance_table
        self.qualified_performance_table = f"{self.schema}.{self.performance_table}"
        self.qualified_renewal_target_table = f"{self.schema}.{self.renewal_target_table}"
        self.qualified_table = self.qualified_performance_table
        self.admin_table = require_identifier(
            env("HOLO_ADMIN_TABLE", "dim_org_admin_user_info_hf"),
            "dim_org_admin_user_info_hf",
        )
        self.qualified_admin_table = f"{self.schema}.{self.admin_table}"
        self._pool: Optional[ThreadedConnectionPool] = None
        self._has_sort_order_column: Dict[str, bool] = {}
        self._has_del_flag_column: Dict[str, bool] = {}
        self._has_period_group_key_column: Dict[str, bool] = {}

    def pool(self) -> ThreadedConnectionPool:
        if self._pool is None:
            self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=int(env("HOLO_MAX_CONNECTIONS", "6")),
                **connection_kwargs(),
            )
        return self._pool

    def close(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None

    def with_connection(self) -> ConnectionContext:
        return ConnectionContext(self.pool())

    def has_sort_order_column(self, table: Optional[str] = None) -> bool:
        table_name = table or self.performance_table
        if table_name in self._has_sort_order_column:
            return self._has_sort_order_column[table_name]

        sql = """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND column_name = 'sort_order'
        LIMIT 1
        """
        self._has_sort_order_column[table_name] = bool(self.fetch_all(sql, [self.schema, table_name]))
        return self._has_sort_order_column[table_name]

    def has_del_flag_column(self, table: Optional[str] = None) -> bool:
        table_name = table or self.performance_table
        if table_name in self._has_del_flag_column:
            return self._has_del_flag_column[table_name]

        sql = """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND column_name = 'del_flag'
        LIMIT 1
        """
        self._has_del_flag_column[table_name] = bool(self.fetch_all(sql, [self.schema, table_name]))
        return self._has_del_flag_column[table_name]

    def has_period_group_key_column(self, table: Optional[str] = None) -> bool:
        table_name = table or self.performance_table
        if table_name in self._has_period_group_key_column:
            return self._has_period_group_key_column[table_name]

        sql = """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND column_name = 'renewal_period_group_key'
        LIMIT 1
        """
        self._has_period_group_key_column[table_name] = bool(self.fetch_all(sql, [self.schema, table_name]))
        return self._has_period_group_key_column[table_name]

    def list_configurations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        module_key = request_module_key(payload)
        if module_key == RENEWAL_TARGET_MODULE_KEY:
            return self.list_renewal_targets(payload)
        if module_key == PERFORMANCE_MODULE_KEY:
            return self.list_performance_configurations(payload)
        raise ValueError(f"不支持的配置模块: {module_key}")

    def list_performance_configurations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        config_month = normalize_month(first_value(payload, "configMonth", "config_month", default=""))
        del_flag = first_value(payload, "delFlag", "del_flag", default=0)
        has_sort_order = self.has_sort_order_column(self.performance_table)
        sort_order_select = "sort_order" if has_sort_order else "0 AS sort_order"
        order_by = (
            "config_month DESC, sort_order ASC NULLS LAST, module ASC"
            if has_sort_order
            else "config_month DESC, module ASC"
        )

        where = ["del_flag = %s"]
        params: List[Any] = [as_smallint(del_flag, 0)]
        if config_month:
            where.append("config_month = %s")
            params.append(config_month)

        sql = f"""
        SELECT
          id,
          create_by,
          update_by,
          create_date,
          update_date,
          config_month,
          module,
          content,
          time_start,
          time_end,
          period1,
          period2,
          periods,
          config_type,
          {sort_order_select},
          del_flag
        FROM {self.qualified_performance_table}
        WHERE {' AND '.join(where)}
        ORDER BY {order_by}
        """

        rows = self.fetch_all(sql, params)
        months = sorted({row["config_month"] for row in rows if row.get("config_month")}, reverse=True)
        return {
            "records": rows,
            "months": months,
            "activeMonth": config_month or (months[0] if months else ""),
        }

    def performance_config_month_for_id(self, record_id: int) -> str:
        sql = f"""
        SELECT config_month
        FROM {self.qualified_performance_table}
        WHERE id = %s
        LIMIT 1
        """
        rows = self.fetch_all(sql, [record_id])
        return normalize_month(rows[0].get("config_month")) if rows else ""

    def list_renewal_targets(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        renewal_period_id = as_int(first_value(payload, "renewalPeriodId", "renewal_period_id", default=None))
        period_options = self.renewal_period_options(only_configured=True)
        available_period_options = self.renewal_period_options()
        has_sort_order = self.has_sort_order_column(self.renewal_target_table)
        has_del_flag = self.has_del_flag_column(self.renewal_target_table)
        has_period_group_key = self.has_period_group_key_column(self.renewal_target_table)
        sort_order_select = "target.sort_order" if has_sort_order else "0 AS sort_order"
        sort_order_order = "target.sort_order ASC NULLS LAST,\n                 " if has_sort_order else ""
        period_group_key_select = (
            "COALESCE(NULLIF(CAST(target.renewal_period_group_key AS text), ''), "
            "CAST(target.renewal_period_id AS text))"
            if has_period_group_key
            else "CAST(target.renewal_period_id AS text)"
        )
        where = ["target.renewal_period_id IS NOT NULL"]
        params: List[Any] = []
        if has_del_flag:
            where.insert(0, "COALESCE(target.del_flag, 0) = 0")
        if renewal_period_id is not None:
            where.append("period.id = %s")
            params.append(renewal_period_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        sql = f"""
        SELECT
          period.id AS renewal_period_id,
          period.period_name AS renewal_period_name,
          {period_group_key_select} AS renewal_period_group_key,
          target.grade,
          COALESCE(target.class_mode, '') AS class_mode,
          COALESCE(target.class_version, '') AS class_version,
          target.all_rate,
          target.s_rate,
          target.a_rate,
          target.b_rate,
          target.c_rate,
          target.d_rate,
          {sort_order_select},
          {"target.del_flag" if has_del_flag else "0 AS del_flag"}
        FROM (
          SELECT
            id,
            max(period_name) AS period_name
          FROM book.db_renewal_period
          WHERE id IS NOT NULL
          GROUP BY id
        ) period
        LEFT JOIN {self.qualified_renewal_target_table} target
          ON target.renewal_period_id = period.id
        {where_sql}
        ORDER BY period.id DESC NULLS LAST,
                 {sort_order_order}
                 target.grade ASC NULLS LAST,
                 target.class_mode ASC NULLS LAST,
                 target.class_version ASC NULLS LAST
        """

        rows = self.fetch_all(sql, params)
        period_ids = [option["id"] for option in period_options]
        return {
            "moduleKey": RENEWAL_TARGET_MODULE_KEY,
            "tableName": self.qualified_renewal_target_table,
            "records": rows,
            "renewalPeriodIds": period_ids,
            "renewalPeriodOptions": period_options,
            "availableRenewalPeriodOptions": available_period_options,
            "activeRenewalPeriodId": renewal_period_id
            or (period_ids[0] if period_ids else (available_period_options[0]["id"] if available_period_options else "")),
        }

    def renewal_period_options(self, only_configured: bool = False) -> List[Dict[str, Any]]:
        if not only_configured:
            sql = """
            SELECT
              period.id,
              max(period.period_name) AS period_name
            FROM book.db_renewal_period period
            WHERE period.id IS NOT NULL
            GROUP BY period.id
            ORDER BY period.id DESC
            """
            rows = self.fetch_all(sql, [])
            return [
                {
                    "id": row["id"],
                    "periodIds": [row["id"]],
                    "periodGroupKey": str(row["id"]),
                    "periodName": str(row.get("period_name") or row["id"]),
                }
                for row in rows
            ]

        has_del_flag = self.has_del_flag_column(self.renewal_target_table)
        has_period_group_key = self.has_period_group_key_column(self.renewal_target_table)
        group_key_select = (
            "COALESCE(NULLIF(CAST(target.renewal_period_group_key AS text), ''), "
            "CAST(target.renewal_period_id AS text))"
            if has_period_group_key
            else "CAST(target.renewal_period_id AS text)"
        )
        where = ["target.renewal_period_id IS NOT NULL"]
        if has_del_flag:
            where.insert(0, "COALESCE(target.del_flag, 0) = 0")

        sql = f"""
        SELECT
          target.renewal_period_id,
          {group_key_select} AS period_group_key,
          max(period.period_name) AS period_name
        FROM {self.qualified_renewal_target_table} target
        JOIN book.db_renewal_period period
          ON period.id = target.renewal_period_id
        WHERE {' AND '.join(where)}
        GROUP BY target.renewal_period_id, {group_key_select}
        ORDER BY target.renewal_period_id DESC
        """
        rows = self.fetch_all(sql, [])
        period_name_map = {
            str(option["id"]): str(option["periodName"])
            for option in self.renewal_period_options(only_configured=False)
        }
        groups: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            period_id = as_int(row.get("renewal_period_id"))
            if period_id is None:
                continue
            group_key = normalize_renewal_period_group_key(
                row.get("period_group_key"),
                period_id,
            )
            if not group_key:
                continue
            group = groups.setdefault(
                group_key,
                {
                    "id": group_key,
                    "periodGroupKey": group_key,
                    "periodIds": renewal_period_group_ids(group_key, period_id),
                    "periodName": "",
                },
            )
            group["periodIds"] = renewal_period_group_ids(
                [*group["periodIds"], period_id],
                period_id,
            )

        options = []
        for group_key, group in groups.items():
            names = [
                period_name_map.get(str(period_id), str(period_id))
                for period_id in group["periodIds"]
            ]
            group["periodName"] = "+".join(names)
            options.append(group)
        options.sort(
            key=lambda option: (
                -(max(option["periodIds"]) if option["periodIds"] else 0),
                option["periodName"],
            )
        )
        return options

    def period_options(self) -> List[Dict[str, str]]:
        sql = """
        SELECT DISTINCT concat(class_year, class_season) AS period_name
        FROM bi.dim_org_box_class_hf b
        WHERE shelf_status = 1
          AND class_year > ''
          AND tag_name = '大班'
          AND is_valen = '正价'
          AND class_name NOT LIKE '%%测试%%'
          AND del_flag = 0
        ORDER BY period_name DESC
        """
        rows = self.fetch_all(sql, [])
        return [{"periodName": row["period_name"]} for row in rows if row.get("period_name")]

    def authenticate_user(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        identifier = str(first_value(
            payload,
            "identifier",
            "mobile",
            "adminId",
            "admin_id",
            "employeeId",
            "employee_id",
            default="",
        )).strip()
        password = str(first_value(payload, "password", default=""))
        if not identifier or not password:
            return None

        sql = f"""
        SELECT
          admin_id,
          mobile,
          status,
          user_name,
          role_id,
          role_name,
          employee_id,
          admin_organ_id,
          organ_name,
          parent_id,
          is_full_view,
          permission_type,
          permission_scope,
          admin_organ_ids,
          parent_ids,
          teacher_uid,
          subject,
          is_group_leader,
          password
        FROM {self.qualified_admin_table}
        WHERE status = 1
          AND (
            mobile = %s
            OR CAST(admin_id AS text) = %s
            OR employee_id = %s
          )
        ORDER BY permission_scope DESC, update_date DESC
        """
        rows = self.fetch_all(sql, [identifier, identifier, identifier])
        if not rows or not any(password_matches(password, row.get("password")) for row in rows):
            return None

        clean_rows = [sanitize_admin_row(row) for row in rows]
        first = clean_rows[0]
        return {
            "adminId": first.get("admin_id"),
            "mobile": first.get("mobile"),
            "userName": first.get("user_name"),
            "rows": clean_rows,
            "canView": has_view_permission(clean_rows),
            "canEdit": has_edit_permission(clean_rows),
        }

    def admin_user_info(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        admin_id = as_int(first_value(payload, "adminId", "admin_id", default=None))
        mobile = str(first_value(payload, "mobile", default="")).strip()
        if admin_id is None and not mobile:
            return []

        where = ["status = 1"]
        params: List[Any] = []
        identity_where = []
        if admin_id is not None:
            identity_where.append("admin_id = %s")
            params.append(admin_id)
        if mobile:
            identity_where.append("mobile = %s")
            params.append(mobile)
        where.append(f"({' OR '.join(identity_where)})")

        sql = f"""
        SELECT
          admin_id,
          mobile,
          status,
          user_name,
          role_id,
          role_name,
          admin_organ_id,
          organ_name,
          parent_id,
          is_full_view,
          permission_type,
          permission_scope,
          admin_organ_ids,
          parent_ids,
          teacher_uid,
          subject,
          is_group_leader
        FROM {self.qualified_admin_table}
        WHERE {' AND '.join(where)}
        ORDER BY permission_scope DESC, update_date DESC
        """
        return [sanitize_admin_row(row) for row in self.fetch_all(sql, params)]

    def batch_upsert(self, payload: Any, operator_id: Optional[int]) -> Dict[str, Any]:
        module_key = request_module_key(payload)
        if module_key == RENEWAL_TARGET_MODULE_KEY:
            return self.batch_upsert_renewal_targets(payload)
        if module_key != PERFORMANCE_MODULE_KEY:
            raise ValueError(f"不支持的配置模块: {module_key}")

        rows = payload if isinstance(payload, list) else payload.get("rows") or payload.get("records") or payload.get("data") or []
        if not isinstance(rows, list):
            raise ValueError("保存参数必须是数组")
        has_sort_order = self.has_sort_order_column(self.performance_table)

        normalized_rows = [
            self.normalize_configuration_row(raw, operator_id)
            for raw in rows
            if isinstance(raw, dict)
        ]
        if not normalized_rows:
            return {"saved": 0}

        locked_months = sorted({row[3] for row in normalized_rows if is_historical_config_month(row[3])})
        if locked_months:
            raise ValueError(f"历史月份已锁定，不能保存: {', '.join(locked_months)}")

        if has_sort_order:
            template = (
                "(%s, %s, COALESCE(%s, now()), now(), %s, %s, %s, %s, %s, "
                "COALESCE(%s, ''), COALESCE(%s, ''), COALESCE(%s, ARRAY[]::text[]), "
                "COALESCE(%s, ''), COALESCE(%s, 0), COALESCE(%s, 0))"
            )
            sql = f"""
            INSERT INTO {self.qualified_performance_table} (
              create_by,
              update_by,
              create_date,
              update_date,
              config_month,
              module,
              content,
              time_start,
              time_end,
              period1,
              period2,
              periods,
              config_type,
              sort_order,
              del_flag
            )
            VALUES %s
            ON CONFLICT (config_month, module)
            DO UPDATE SET
              update_by = EXCLUDED.update_by,
              update_date = now(),
              content = EXCLUDED.content,
              time_start = EXCLUDED.time_start,
              time_end = EXCLUDED.time_end,
              period1 = EXCLUDED.period1,
              period2 = EXCLUDED.period2,
              periods = EXCLUDED.periods,
              config_type = EXCLUDED.config_type,
              sort_order = EXCLUDED.sort_order,
              del_flag = EXCLUDED.del_flag
            """
        else:
            normalized_rows = [row[:-2] + (row[-1],) for row in normalized_rows]
            template = (
                "(%s, %s, COALESCE(%s, now()), now(), %s, %s, %s, %s, %s, "
                "COALESCE(%s, ''), COALESCE(%s, ''), COALESCE(%s, ARRAY[]::text[]), "
                "COALESCE(%s, ''), COALESCE(%s, 0))"
            )
            sql = f"""
            INSERT INTO {self.qualified_performance_table} (
              create_by,
              update_by,
              create_date,
              update_date,
              config_month,
              module,
              content,
              time_start,
              time_end,
              period1,
              period2,
              periods,
              config_type,
              del_flag
            )
            VALUES %s
            ON CONFLICT (config_month, module)
            DO UPDATE SET
              update_by = EXCLUDED.update_by,
              update_date = now(),
              content = EXCLUDED.content,
              time_start = EXCLUDED.time_start,
              time_end = EXCLUDED.time_end,
              period1 = EXCLUDED.period1,
              period2 = EXCLUDED.period2,
              periods = EXCLUDED.periods,
              config_type = EXCLUDED.config_type,
              del_flag = EXCLUDED.del_flag
            """

        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(
                    cursor,
                    sql,
                    normalized_rows,
                    template=template,
                    page_size=len(normalized_rows),
                )
            conn.commit()

        return {
            "saved": len(normalized_rows),
        }

    def batch_upsert_renewal_targets(self, payload: Any) -> Dict[str, Any]:
        rows = payload if isinstance(payload, list) else payload.get("rows") or payload.get("records") or payload.get("data") or []
        if not isinstance(rows, list):
            raise ValueError("续报目标保存参数必须是数组")

        normalized_rows = [
            self.normalize_renewal_target_row(raw)
            for raw in rows
            if isinstance(raw, dict)
        ]
        if not normalized_rows:
            return {"saved": 0, "deleted": 0}

        has_sort_order = self.has_sort_order_column(self.renewal_target_table)
        has_period_group_key = self.has_period_group_key_column(self.renewal_target_table)
        sort_order_set = ", sort_order = %s" if has_sort_order else ""
        sort_order_column = ", sort_order" if has_sort_order else ""
        sort_order_value = ", %s" if has_sort_order else ""
        period_group_key_set = ", renewal_period_group_key = %s" if has_period_group_key else ""
        period_group_key_column = ", renewal_period_group_key" if has_period_group_key else ""
        period_group_key_value = ", %s" if has_period_group_key else ""
        has_del_flag = self.has_del_flag_column(self.renewal_target_table)
        del_flag_set = ", del_flag = 0" if has_del_flag else ""
        del_flag_column = ", del_flag" if has_del_flag else ""
        del_flag_value = ", 0" if has_del_flag else ""
        group_key_where = "renewal_period_group_key = %s AND " if has_period_group_key else ""
        update_sql = f"""
        UPDATE {self.qualified_renewal_target_table}
        SET
          renewal_period_id = %s,
          grade = %s,
          class_mode = %s,
          class_version = %s,
          all_rate = %s,
          s_rate = %s,
          a_rate = %s,
          b_rate = %s,
          c_rate = %s,
          d_rate = %s
          {period_group_key_set}
          {sort_order_set}
          {del_flag_set}
        WHERE {group_key_where}renewal_period_id = %s
          AND grade = %s
          AND COALESCE(class_mode, '') = %s
          AND COALESCE(class_version, '') = %s
        """
        insert_sql = f"""
        INSERT INTO {self.qualified_renewal_target_table} (
          renewal_period_id,
          grade,
          class_mode,
          class_version,
          all_rate,
          s_rate,
          a_rate,
          b_rate,
          c_rate,
          d_rate
          {period_group_key_column}
          {sort_order_column}
          {del_flag_column}
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s{period_group_key_value}{sort_order_value}{del_flag_value})
        """
        delete_sql = None
        if has_del_flag:
            delete_sql = f"""
            UPDATE {self.qualified_renewal_target_table}
            SET del_flag = 1
            WHERE {group_key_where}renewal_period_id = %s
              AND grade = %s
              AND COALESCE(class_mode, '') = %s
              AND COALESCE(class_version, '') = %s
              AND COALESCE(del_flag, 0) = 0
            """

        saved = 0
        deleted = 0
        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                for row in normalized_rows:
                    values = row["values"]
                    key = ((row["period_group_key"],) if has_period_group_key else ()) + row["key"]
                    original_key = (
                        ((row["original_period_group_key"],) if has_period_group_key else ())
                        + (row["original_key"] or row["key"])
                    )
                    if row["deleted"]:
                        if delete_sql is None:
                            raise ValueError("续报目标表缺少 del_flag 字段，请先执行 db/renewal_target_rate.sql")
                        cursor.execute(delete_sql, original_key)
                        deleted += cursor.rowcount
                        continue

                    write_values = values
                    if has_period_group_key:
                        write_values += (row["period_group_key"],)
                    if has_sort_order:
                        write_values += (row["sort_order"],)
                    cursor.execute(update_sql, write_values + original_key)
                    affected = cursor.rowcount
                    if affected == 0 and original_key != key:
                        cursor.execute(update_sql, write_values + key)
                        affected = cursor.rowcount
                    if affected == 0:
                        cursor.execute(insert_sql, write_values)
                    saved += 1
            conn.commit()

        return {"saved": saved, "deleted": deleted}

    def logical_delete(self, payload: Dict[str, Any], operator_id: Optional[int]) -> Dict[str, int]:
        module_key = request_module_key(payload)
        if module_key == RENEWAL_TARGET_MODULE_KEY:
            return self.delete_renewal_target(payload)
        if module_key != PERFORMANCE_MODULE_KEY:
            raise ValueError(f"不支持的配置模块: {module_key}")

        record_id = as_int(first_value(payload, "id", default=None))
        config_month = normalize_month(first_value(payload, "configMonth", "config_month", default=""))
        module = str(first_value(payload, "module", default="")).strip()

        if record_id is None and (not config_month or not module):
            raise ValueError("删除需要 id，或 configMonth + module")

        target_month = self.performance_config_month_for_id(record_id) if record_id is not None else config_month
        if is_historical_config_month(target_month):
            raise ValueError(f"历史月份已锁定，不能删除: {target_month}")

        if record_id is not None:
            sql = f"""
            UPDATE {self.qualified_table}
            SET del_flag = 1, update_by = %s, update_date = now()
            WHERE id = %s
            """
            params: Tuple[Any, ...] = (operator_id, record_id)
        else:
            sql = f"""
            UPDATE {self.qualified_table}
            SET del_flag = 1, update_by = %s, update_date = now()
            WHERE config_month = %s AND module = %s
            """
            params = (operator_id, config_month, module)

        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                affected = cursor.rowcount
            conn.commit()
        return {"deleted": affected}

    def delete_renewal_target(self, payload: Dict[str, Any]) -> Dict[str, int]:
        row = self.normalize_renewal_target_row(payload)
        has_period_group_key = self.has_period_group_key_column(self.renewal_target_table)
        key = (
            ((row["original_period_group_key"],) if has_period_group_key else ())
            + (row["original_key"] or row["key"])
        )
        if not self.has_del_flag_column(self.renewal_target_table):
            raise ValueError("续报目标表缺少 del_flag 字段，请先执行 db/renewal_target_rate.sql")
        group_key_where = "renewal_period_group_key = %s AND " if has_period_group_key else ""
        sql = f"""
        UPDATE {self.qualified_renewal_target_table}
        SET del_flag = 1
        WHERE {group_key_where}renewal_period_id = %s
          AND grade = %s
          AND COALESCE(class_mode, '') = %s
          AND COALESCE(class_version, '') = %s
          AND COALESCE(del_flag, 0) = 0
        """
        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, key)
                affected = cursor.rowcount
            conn.commit()
        return {"deleted": affected}

    def normalize_configuration_row(self, row: Dict[str, Any], operator_id: Optional[int]) -> Tuple[Any, ...]:
        config_month = normalize_month(first_value(row, "configMonth", "config_month"))
        module = str(first_value(row, "module")).strip()
        if not config_month or not module:
            raise ValueError("configMonth 和 module 不能为空")

        create_by = as_int(first_value(row, "createBy", "create_by", default=None)) or operator_id
        update_by = as_int(first_value(row, "updateBy", "update_by", default=None)) or operator_id
        create_date = parse_datetime(first_value(row, "createDate", "create_date", default=None))
        period1, period2, periods = normalize_period_fields(row, module)
        config_type = str(first_value(row, "configType", "config_type", default="")).strip()
        if module not in CONFIG_TYPE_MODULES:
            config_type = ""
        elif config_type not in CONFIG_TYPE_VALUES:
            config_type = "常规"

        return (
            create_by,
            update_by,
            create_date,
            config_month,
            module,
            str(first_value(row, "content", default="")),
            parse_date(first_value(row, "timeStart", "time_start", default=None)),
            parse_date(first_value(row, "timeEnd", "time_end", default=None)),
            period1,
            period2,
            periods,
            config_type,
            as_int(first_value(row, "sortOrder", "sort_order", default=None)),
            as_smallint(first_value(row, "delFlag", "del_flag", default=0), 0),
        )

    def normalize_renewal_target_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        renewal_period_id = as_int(first_value(row, "renewalPeriodId", "renewal_period_id", default=None))
        grade = as_int(first_value(row, "grade", default=None))
        if renewal_period_id is None or grade is None:
            raise ValueError("renewalPeriodId 和 grade 不能为空")

        class_mode = str(first_value(row, "classMode", "class_mode", default="")).strip()
        class_version = str(first_value(row, "classVersion", "class_version", default="")).strip()
        key = (renewal_period_id, grade, class_mode, class_version)
        period_group_key = normalize_renewal_period_group_key(
            first_value(
                row,
                "renewalPeriodGroupKey",
                "renewal_period_group_key",
                "periodGroupKey",
                "period_group_key",
                default="",
            ),
            renewal_period_id,
        )

        original_period_id = as_int(first_value(row, "originalRenewalPeriodId", "original_renewal_period_id", default=None))
        original_grade = as_int(first_value(row, "originalGrade", "original_grade", default=None))
        original_class_mode = str(first_value(row, "originalClassMode", "original_class_mode", default=class_mode)).strip()
        original_class_version = str(first_value(row, "originalClassVersion", "original_class_version", default=class_version)).strip()
        original_key = None
        if original_period_id is not None and original_grade is not None:
            original_key = (original_period_id, original_grade, original_class_mode, original_class_version)
        original_period_group_key = normalize_renewal_period_group_key(
            first_value(
                row,
                "originalRenewalPeriodGroupKey",
                "original_renewal_period_group_key",
                "originalPeriodGroupKey",
                "original_period_group_key",
                default="",
            ),
            original_period_id or renewal_period_id,
        )

        values = (
            renewal_period_id,
            grade,
            class_mode,
            class_version,
            parse_decimal(first_value(row, "allRate", "all_rate", default=None)),
            parse_decimal(first_value(row, "sRate", "s_rate", default=None)),
            parse_decimal(first_value(row, "aRate", "a_rate", default=None)),
            parse_decimal(first_value(row, "bRate", "b_rate", default=None)),
            parse_decimal(first_value(row, "cRate", "c_rate", default=None)),
            parse_decimal(first_value(row, "dRate", "d_rate", default=None)),
        )
        sort_order = as_int(first_value(row, "sortOrder", "sort_order", default=None)) or 0

        return {
            "values": values,
            "key": key,
            "original_key": original_key,
            "period_group_key": period_group_key,
            "original_period_group_key": original_period_group_key,
            "sort_order": sort_order,
            "deleted": bool(row.get("_delete") or row.get("delete"))
            or as_smallint(first_value(row, "delFlag", "del_flag", default=0), 0) == 1,
        }

    def fetch_all(self, sql: str, params: Iterable[Any]) -> List[Dict[str, Any]]:
        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(params))
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]


class PerformanceConfigurationHandler(BaseHTTPRequestHandler):
    repository = PerformanceConfigurationRepository()
    session_cookie_name = "qdata_session"
    session_max_age = int(env("SESSION_MAX_AGE_SECONDS", "28800"))
    sessions: Dict[str, Dict[str, Any]] = {}

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.add_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/data_set/performance/configuration/health":
            self.send_json({"ok": True})
            return
        if parsed.path == "/data_set/performance/configuration/me":
            user = self.current_session_user()
            if user is None:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录")
                return
            self.send_json(user)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        routes = {
            "/data_set/performance/configuration/login": self.handle_login,
            "/data_set/performance/configuration/logout": self.handle_logout,
            "/data_set/performance/configuration/list": self.handle_list,
            "/data_set/performance/configuration/periodOptions": self.handle_period_options,
            "/data_set/performance/configuration/adminUserInfo": self.handle_admin_user_info,
            "/data_set/performance/configuration/batchUpsert": self.handle_batch_upsert,
            "/data_set/performance/configuration/delete": self.handle_delete,
        }
        handler = routes.get(parsed.path)
        if handler is None:
            self.send_error_json(HTTPStatus.NOT_FOUND, "接口不存在")
            return

        try:
            payload = parse_json_body(self)
            if parsed.path not in {
                "/data_set/performance/configuration/login",
                "/data_set/performance/configuration/logout",
            }:
                user = self.current_session_user()
                if user is None:
                    self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录")
                    return
                if parsed.path in {
                    "/data_set/performance/configuration/batchUpsert",
                    "/data_set/performance/configuration/delete",
                } and not user.get("canEdit"):
                    self.send_error_json(HTTPStatus.FORBIDDEN, "暂无编辑权限")
                    return
            handler(payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc) or "参数错误")
        except Exception as exc:
            traceback.print_exc()
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc) or "服务器异常")

    def handle_login(self, payload: Dict[str, Any]) -> None:
        body = payload if isinstance(payload, dict) else {}
        user = self.repository.authenticate_user(body)
        if user is None:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "账号或密码不正确")
            return

        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "user": user,
            "expires_at": time.time() + self.session_max_age,
        }
        next_path = safe_next_path(str(first_value(body, "next", default="/performance-configuration.html")))
        self.send_json(
            {"user": user, "next": next_path},
            extra_headers={
                "Set-Cookie": self.session_cookie(token, self.session_max_age),
            },
        )

    def handle_logout(self, payload: Dict[str, Any]) -> None:
        token = self.cookie_value(self.session_cookie_name)
        if token:
            self.sessions.pop(token, None)
        self.send_json(
            {"ok": True},
            extra_headers={
                "Set-Cookie": self.session_cookie("", 0),
            },
        )

    def handle_list(self, payload: Dict[str, Any]) -> None:
        body = payload if isinstance(payload, dict) else {}
        self.send_json(self.repository.list_configurations(body))

    def handle_period_options(self, payload: Dict[str, Any]) -> None:
        self.send_json(self.repository.period_options())

    def handle_admin_user_info(self, payload: Dict[str, Any]) -> None:
        body = payload if isinstance(payload, dict) else {}
        if not first_value(body, "adminId", "admin_id", "mobile", default=""):
            user = self.current_session_user()
            if user is None:
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "请先登录")
                return
            self.send_json(user.get("rows", []))
            return
        self.send_json(self.repository.admin_user_info(body))

    def handle_batch_upsert(self, payload: Any) -> None:
        self.send_json(self.repository.batch_upsert(payload, self.operator_id()))

    def handle_delete(self, payload: Dict[str, Any]) -> None:
        body = payload if isinstance(payload, dict) else {}
        self.send_json(self.repository.logical_delete(body, self.operator_id()))

    def operator_id(self) -> Optional[int]:
        user = self.current_session_user()
        if user is not None:
            session_admin_id = as_int(user.get("adminId"))
            if session_admin_id is not None:
                return session_admin_id
        for header in ("x-admin-id", "admin-id", "user-id"):
            number = as_int(self.headers.get(header))
            if number is not None:
                return number
        return None

    def serve_static(self, request_path: str) -> None:
        path = unquote(request_path)
        if path in ("", "/"):
            path = "/performance-configuration.html"

        target = (WEB_ROOT / path.lstrip("/")).resolve()
        if WEB_ROOT not in target.parents and target != WEB_ROOT:
            self.send_error_json(HTTPStatus.FORBIDDEN, "禁止访问")
            return
        if not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if target.name == "performance-configuration.html" and self.current_session_user() is None:
            self.send_redirect("/login.html?next=/performance-configuration.html")
            return

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.name == "performance-configuration.html":
            body = self.performance_page_body(target)
        else:
            body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.add_common_headers(content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def performance_page_body(self, target: Path) -> bytes:
        bootstrap = """
  <script>
    window.PERFORMANCE_CONFIGURATION_API_BASE = "/data_set/performance/configuration";
  </script>
"""
        html = target.read_text(encoding="utf-8")
        if bootstrap.strip() in html:
            return html.encode("utf-8")
        return html.replace("  <script>\n", f"{bootstrap}\n  <script>\n", 1).encode("utf-8")

    def send_json(
        self,
        data: Any,
        status: HTTPStatus = HTTPStatus.OK,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        body = json.dumps({"code": 0, "message": "success", "data": data}, ensure_ascii=False, default=json_default).encode("utf-8")
        self.send_response(status)
        self.add_common_headers("application/json; charset=utf-8")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"code": int(status), "message": message, "data": None}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.add_common_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def add_common_headers(self, content_type: Optional[str] = None) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, token, x-admin-id, admin-id, user-id")
        self.send_header("Cache-Control", "no-store")
        if content_type:
            self.send_header("Content-Type", content_type)

    def send_redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.add_common_headers()
        self.send_header("Location", location)
        self.end_headers()

    def cookie_value(self, name: str) -> str:
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            key, _, value = part.strip().partition("=")
            if key == name:
                return value
        return ""

    def current_session_user(self) -> Optional[Dict[str, Any]]:
        token = self.cookie_value(self.session_cookie_name)
        if not token:
            return None
        session = self.sessions.get(token)
        if not session:
            return None
        if time.time() > float(session.get("expires_at", 0)):
            self.sessions.pop(token, None)
            return None
        return session.get("user")

    def session_cookie(self, token: str, max_age: int) -> str:
        return f"{self.session_cookie_name}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="绩效配置本地后端")
    parser.add_argument("--host", default=env("BACKEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(env("BACKEND_PORT", "8010")))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), PerformanceConfigurationHandler)
    public_url = env("PUBLIC_URL", f"http://{args.host}:{args.port}").rstrip("/")
    app_name = env("APP_NAME", "绩效配置")
    print(f"{app_name} 服务已启动: {public_url}/performance-configuration.html")
    print("API: /data_set/performance/configuration/login /me /list /periodOptions /adminUserInfo /batchUpsert /delete")
    try:
        server.serve_forever()
    finally:
        PerformanceConfigurationHandler.repository.close()


if __name__ == "__main__":
    main()
