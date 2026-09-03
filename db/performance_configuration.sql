CREATE SCHEMA IF NOT EXISTS bi;

CREATE TABLE IF NOT EXISTS bi.performance_configuration (
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
  periods text[] NOT NULL DEFAULT ARRAY[]::text[],
  config_type varchar(32) NOT NULL DEFAULT '',
  del_flag smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (config_month, module)
);

COMMENT ON TABLE bi.performance_configuration IS '绩效配置表';
COMMENT ON COLUMN bi.performance_configuration.create_by IS '创建人后台用户ID';
COMMENT ON COLUMN bi.performance_configuration.update_by IS '更新人后台用户ID';
COMMENT ON COLUMN bi.performance_configuration.create_date IS '创建时间';
COMMENT ON COLUMN bi.performance_configuration.update_date IS '更新时间';
COMMENT ON COLUMN bi.performance_configuration.config_month IS '配置月份，按 yyyy-mm 保存，例如 2026-08';
COMMENT ON COLUMN bi.performance_configuration.module IS '配置模块，例如 带生数';
COMMENT ON COLUMN bi.performance_configuration.content IS '前端维护的指标口径说明，按换行保存，可为空';
COMMENT ON COLUMN bi.performance_configuration.time_start IS '配置适用开始日期';
COMMENT ON COLUMN bi.performance_configuration.time_end IS '配置适用结束日期';
COMMENT ON COLUMN bi.performance_configuration.period1 IS '期别 1，例如 2026秋；多个期别可逗号组合';
COMMENT ON COLUMN bi.performance_configuration.period2 IS '期别 2，例如 2026暑';
COMMENT ON COLUMN bi.performance_configuration.periods IS '期别数组，例如 ARRAY[''2026秋'', ''2026暑'']，用于 ANY/&& 查询';
COMMENT ON COLUMN bi.performance_configuration.config_type IS '配置类型，例如 常规，没有类型时为空字符串';
COMMENT ON COLUMN bi.performance_configuration.del_flag IS '逻辑删除标记，0 未删除，1 已删除';


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
  del_flag
FROM bi.performance_configuration
WHERE del_flag = 0
  AND (
    :configMonth IS NULL
    OR config_month = :configMonth
  )
ORDER BY
  config_month DESC,
  module ASC,
  period1 DESC,
  period2 DESC,
  config_type ASC;

-- Upsert example. Java/JSON fields use camelCase:
-- configMonth uses yyyy-mm, for example 2026-08.
-- Other Java/JSON fields use camelCase:
-- configType, timeStart, timeEnd, createBy, updateBy, createDate, updateDate, delFlag.
INSERT INTO bi.performance_configuration (
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
VALUES (
  :createBy,
  :updateBy,
  coalesce(:createDate, now()),
  now(),
  :configMonth,
  :module,
  :content,
  :timeStart,
  :timeEnd,
  coalesce(:period1, ''),
  coalesce(:period2, ''),
  coalesce(:periods, ARRAY[]::text[]),
  coalesce(:configType, ''),
  coalesce(:delFlag, 0)
)
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
  del_flag = EXCLUDED.del_flag;

-- Logical delete by primary key.
UPDATE bi.performance_configuration
SET
  del_flag = 1,
  update_by = :updateBy,
  update_date = now()
WHERE id = :id;

-- Logical delete by business key.
UPDATE bi.performance_configuration
SET
  del_flag = 1,
  update_by = :updateBy,
  update_date = now()
WHERE config_month = :configMonth
  AND module = :module;
