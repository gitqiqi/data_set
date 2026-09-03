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


def as_smallint(value: Any, default: int = 0) -> int:
    number = as_int(value)
    return default if number is None else number


def first_value(row: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def normalize_period_text(value: Any) -> str:
    values = []
    for part in re.split(r"[,，、/]", str(value or "")):
        text = part.strip()
        if not text:
            continue
        text = re.sub(r"^(\d{2})(?=[\u4e00-\u9fa5])", r"20\1", text)
        values.append(text)
    return ",".join(dict.fromkeys(values))


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
        self.table = require_identifier(env("HOLO_TABLE", "performance_configuration"), "performance_configuration")
        self.qualified_table = f"{self.schema}.{self.table}"
        self.admin_table = require_identifier(
            env("HOLO_ADMIN_TABLE", "dim_org_admin_user_info_hf"),
            "dim_org_admin_user_info_hf",
        )
        self.qualified_admin_table = f"{self.schema}.{self.admin_table}"
        self._pool: Optional[ThreadedConnectionPool] = None
        self._table_ready = False

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

    def ensure_table(self) -> None:
        if self._table_ready:
            return

        create_sql = f"""
        CREATE SCHEMA IF NOT EXISTS {self.schema};

        CREATE TABLE IF NOT EXISTS {self.qualified_table} (
          id bigserial,
          create_by bigint,
          update_by bigint,
          create_date timestamptz NOT NULL DEFAULT now(),
          update_date timestamptz NOT NULL DEFAULT now(),
          config_month varchar(7) NOT NULL,
          module varchar(64) NOT NULL,
          content text,
          time_start date,
          time_end date,
          period1 varchar(64) NOT NULL DEFAULT '',
          period2 varchar(64) NOT NULL DEFAULT '',
          config_type varchar(32) NOT NULL DEFAULT '',
          del_flag smallint NOT NULL DEFAULT 0,
          PRIMARY KEY (config_month, module)
        )
        """
        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_sql)
            conn.commit()
        self._table_ready = True

    def list_configurations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_table()
        config_month = normalize_month(first_value(payload, "configMonth", "config_month", "month", default=""))
        del_flag = first_value(payload, "delFlag", "del_flag", default=0)

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
          config_type,
          del_flag
        FROM {self.qualified_table}
        WHERE {' AND '.join(where)}
        ORDER BY config_month DESC, module ASC
        """

        rows = self.fetch_all(sql, params)
        months = sorted({row["config_month"] for row in rows if row.get("config_month")}, reverse=True)
        return {
            "records": rows,
            "months": months,
            "activeMonth": config_month or (months[0] if months else ""),
        }

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
        self.ensure_table()
        rows = payload if isinstance(payload, list) else payload.get("rows") or payload.get("records") or payload.get("data") or []
        if not isinstance(rows, list):
            raise ValueError("保存参数必须是数组")

        normalized_rows = [
            self.normalize_configuration_row(raw, operator_id)
            for raw in rows
            if isinstance(raw, dict)
        ]
        if not normalized_rows:
            return {"saved": 0}

        sql = f"""
        INSERT INTO {self.qualified_table} (
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
          config_type = EXCLUDED.config_type,
          del_flag = EXCLUDED.del_flag
        """

        with self.with_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(
                    cursor,
                    sql,
                    normalized_rows,
                    template="(%s, %s, COALESCE(%s, now()), now(), %s, %s, %s, %s, %s, COALESCE(%s, ''), COALESCE(%s, ''), COALESCE(%s, ''), COALESCE(%s, 0))",
                    page_size=len(normalized_rows),
                )
            conn.commit()

        return {
            "saved": len(normalized_rows),
        }

    def logical_delete(self, payload: Dict[str, Any], operator_id: Optional[int]) -> Dict[str, int]:
        self.ensure_table()
        record_id = as_int(first_value(payload, "id", default=None))
        config_month = normalize_month(first_value(payload, "configMonth", "config_month", "month", default=""))
        module = str(first_value(payload, "module", default="")).strip()

        if record_id is None and (not config_month or not module):
            raise ValueError("删除需要 id，或 configMonth + module")

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

    def normalize_configuration_row(self, row: Dict[str, Any], operator_id: Optional[int]) -> Tuple[Any, ...]:
        config_month = normalize_month(first_value(row, "configMonth", "config_month", "month"))
        module = str(first_value(row, "module")).strip()
        if not config_month or not module:
            raise ValueError("configMonth 和 module 不能为空")

        create_by = as_int(first_value(row, "createBy", "create_by", default=None)) or operator_id
        update_by = as_int(first_value(row, "updateBy", "update_by", default=None)) or operator_id
        create_date = parse_datetime(first_value(row, "createDate", "create_date", "create_time", default=None))

        return (
            create_by,
            update_by,
            create_date,
            config_month,
            module,
            str(first_value(row, "content", default="")),
            parse_date(first_value(row, "timeStart", "time_start", default=None)),
            parse_date(first_value(row, "timeEnd", "time_end", default=None)),
            normalize_period_text(first_value(row, "period1", default="")),
            normalize_period_text(first_value(row, "period2", default="")),
            str(first_value(row, "configType", "config_type", "type", default="")).strip(),
            as_smallint(first_value(row, "delFlag", "del_flag", default=0), 0),
        )

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
    window.PERFORMANCE_CONFIGURATION_ENABLE_AUTH = true;
    window.PERFORMANCE_CONFIGURATION_REMOTE_AUTH = true;
    window.PERFORMANCE_CONFIGURATION_REMOTE_DATA = true;
    window.PERFORMANCE_CONFIGURATION_REMOTE_SAVE = true;
    window.PERFORMANCE_CONFIGURATION_REMOTE_PERIODS = true;
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
