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
  sort_order integer NOT NULL DEFAULT 0,
  del_flag smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (config_month, module)
);

ALTER TABLE bi.performance_configuration
  ADD COLUMN IF NOT EXISTS periods text[];

ALTER TABLE bi.performance_configuration
  ADD COLUMN IF NOT EXISTS sort_order integer NOT NULL DEFAULT 0;

ALTER TABLE bi.performance_configuration
  ALTER COLUMN sort_order SET DEFAULT 0;

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
COMMENT ON COLUMN bi.performance_configuration.period1 IS '首个期别；普通指标为多选期别中的首期，带生数为第一个期别';
COMMENT ON COLUMN bi.performance_configuration.period2 IS '期别 2；仅带生数使用';
COMMENT ON COLUMN bi.performance_configuration.periods IS '页面选择的期别数组；普通指标支持多选，带生数由 period1/period2 汇总，例如 ARRAY[''2026秋'', ''2026暑'']，用于 ANY/&& 查询';
COMMENT ON COLUMN bi.performance_configuration.config_type IS '配置类型，例如 常规，没有类型时为空字符串';
COMMENT ON COLUMN bi.performance_configuration.sort_order IS '同一配置月份下的指标展示顺序';
COMMENT ON COLUMN bi.performance_configuration.del_flag IS '逻辑删除标记，0 未删除，1 已删除';

UPDATE bi.performance_configuration
SET periods = COALESCE(
  regexp_split_to_array(
    NULLIF(regexp_replace(concat_ws(',', NULLIF(period1, ''), NULLIF(period2, '')), '\s+', '', 'g'), ''),
    '[,，、/]'
  ),
  ARRAY[]::text[]
)
WHERE periods IS NULL;

WITH ordered AS (
  SELECT
    config_month,
    module,
    row_number() OVER (PARTITION BY config_month ORDER BY module ASC) AS row_order
  FROM bi.performance_configuration
)
UPDATE bi.performance_configuration target
SET sort_order = ordered.row_order
FROM ordered
WHERE target.config_month = ordered.config_month
  AND target.module = ordered.module
  AND COALESCE(target.sort_order, 0) = 0;

ALTER TABLE bi.performance_configuration
  ALTER COLUMN sort_order SET NOT NULL;

-- Period query examples:
-- WHERE '2026暑' = ANY(periods)
-- WHERE periods && ARRAY['2026暑', '2026秋']
