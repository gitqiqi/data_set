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

ALTER TABLE bi.performance_configuration
  ADD COLUMN IF NOT EXISTS periods text[] NOT NULL DEFAULT ARRAY[]::text[];

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
COMMENT ON COLUMN bi.performance_configuration.period1 IS '旧期别兼容列，由 periods 派生';
COMMENT ON COLUMN bi.performance_configuration.period2 IS '旧期别兼容列，由 periods 派生';
COMMENT ON COLUMN bi.performance_configuration.periods IS '当前期别数组，例如 ARRAY[''2026秋'', ''2026暑'']，用于 ANY/&& 查询';
COMMENT ON COLUMN bi.performance_configuration.config_type IS '配置类型，例如 常规，没有类型时为空字符串';
COMMENT ON COLUMN bi.performance_configuration.del_flag IS '逻辑删除标记，0 未删除，1 已删除';

UPDATE bi.performance_configuration
SET periods = ARRAY(
  SELECT DISTINCT btrim(period_name)
  FROM unnest(regexp_split_to_array(concat_ws(',', period1, period2), '[,，、/]')) AS period_name
  WHERE btrim(period_name) <> ''
)
WHERE periods IS NULL
   OR cardinality(periods) = 0;

-- Period query examples:
-- WHERE '2026暑' = ANY(periods)
-- WHERE periods && ARRAY['2026暑', '2026秋']
