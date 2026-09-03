-- Generated from /Users/cherry/Downloads/export (99).xlsx
-- Target table: bi.performance_configuration
-- config_month format: yyyy-mm

START TRANSACTION;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '带生数',
  '历史学生上课次数：历史期别课消人次  
历史学生上课程数：历史期别课消的总节数  
历史助教均上课人数：历史学生上课次数/历史期别课消的总节数 
历史学生数：历史期别班级最后一次课程里面课消的人数    
去重总带生数：历史学生 + 筛选开始月月末前接新学生去重  
本月月末前接新数：筛选开始月末前接新学生
日均接新数：(本月10号前接新数 + 本月20号前接新数 + 本月月末前接新数) / 3  
日均去重接新数：(本月10号前去重接新数 + 本月20号前去重接新数 + 本月月末前去重接新数) / 3  
汇总带生数：历史助教均上课人数+日均接新数  
汇总去重带生数：历史助教均上课人数+日均去重接新数',
  '2026-08-01',
  '2026-08-31',
  '2026秋',
  '2026暑',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '课前退',
  '筛选时间：按入班时间和退费完成时间
入班时间：按期别，分科目在所选期别内,末次入班时间 总单数：班级订单课消为0或者本月退费类型为课前退
助教：退费前最后入班对应的助教老师信息
分子剔除无效退，分母不剔除',
  '2026-05-18',
  '2026-06-23',
  '202026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '试听退',
  '筛选时间：按下单时间
课消时间：按期别，分科目首次课消在所选期别内
分子剔除无效退，分母不剔除。
最后班级维护助教',
  '2026-05-18',
  '2026-08-15',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '课中退',
  '时间：课消时间&退费完成时间
期别：最后课消在期别范围内 更新频率：小时级

助教取学生最后一次课消，课程的助教老师；班级取学生最后一次课消课程的班级 ，剔除调课调入学生 退费转班取倒数第二次课消的课程数据',
  '2026-08-01',
  '2026-08-31',
  '2026春,2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '学员回访',
  '通话剔除未购买大班通话
快速课限制在班学生
通话次数：外呼、企微联系人助教外呼的人数
5分钟通话次数：外呼、企微联系人助教有外呼>=5分钟的次数
5分钟通话人数：外呼、企微联系人助教有外呼>=5分钟的人数
快速课堂覆盖人数：快速课对应助教老师学生有被拨打过的人数(拨打人可不对应课程助教）
5分钟快速课堂覆盖人数：快速课对应助教老师学生有被拨打时长>=5分钟的人数(拨打人可不对应课程助教）
5分钟通话总人数：5分钟通话人数+5分钟快速课堂覆盖人数（人头去重）',
  '2026-07-01',
  '2026-08-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '新生通话',
  '首次添加好友时课消<=2
筛选时间为首次加微时间
同年级在读正常维护当前在其手上在班学生 退费的学生',
  '2026-05-18',
  '2026-08-24',
  '2026暑,2026秋',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '刷题班上课数据',
  NULL,
  '2026-08-01',
  '2026-08-31',
  '202026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '刷题班课中退',
  NULL,
  '2026-08-01',
  '2026-08-31',
  '202026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '刷题班试听退',
  NULL,
  '2026-06-26',
  '2026-08-15',
  '202026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '小灶课',
  '限制在小灶课圈定学员
选班率:选班人数/小灶课学员数
实际完课数:直播完课数
有效小灶课数：2026暑正价班的入班时间≤7.31 且未退费
有效完课数:2026暑正价班的入班时间≤7.31 且未退费 直播完课人数 实际完课率：直播完课数/直播到课数
有效完课率：有效完课数/小灶课应到数
有效覆盖率：有效完课数/有效小灶课人数 实际覆盖率:直播完课数/小灶课学员数
到课完课限制已结束课程',
  NULL,
  NULL,
  '202026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-08',
  '上课数据',
  NULL,
  '2026-07-01',
  '2026-08-31',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '带生数',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '2026春',
  '2026春',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '助教班课数据',
  NULL,
  '2026-03-02',
  '2026-03-22',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '课中退',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '2026春,2026寒1期,2026寒2期',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '试听退',
  NULL,
  '2026-02-01',
  '2026-03-15',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '学员回访',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-04',
  '新生通话',
  NULL,
  '2026-02-24',
  '2026-03-24',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '带生数',
  NULL,
  '2026-07-01',
  '2026-07-31',
  '2026暑',
  '2026暑',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '课前退',
  NULL,
  '2026-05-18',
  '2026-06-23',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '试听退',
  NULL,
  '2026-05-18',
  '2026-08-07',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '课中退',
  NULL,
  '2026-07-01',
  '2026-08-31',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '学员回访',
  NULL,
  '2026-07-01',
  '2026-07-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '新生通话',
  NULL,
  '2026-06-24',
  '2026-07-23',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-07',
  '上课数据',
  NULL,
  '2026-07-04',
  '2026-08-19',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '带生数',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '2026春',
  '2026春',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '助教班课数据',
  NULL,
  '2026-03-02',
  '2026-03-22',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '课中退',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '2026春,2026寒',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '试听退',
  NULL,
  '2026-02-01',
  '2026-03-15',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '学员回访',
  NULL,
  '2026-03-01',
  '2026-03-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-03',
  '新生通话',
  NULL,
  '2026-02-24',
  '2026-03-24',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '带生数',
  NULL,
  '2026-05-01',
  '2026-05-31',
  '2026春',
  '2026暑',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '助教班课数据',
  NULL,
  '2026-04-24',
  '2026-05-24',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '课中退',
  NULL,
  '2026-05-01',
  '2026-05-31',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '试听退',
  NULL,
  '2026-04-16',
  '2026-05-15',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '学员回访',
  NULL,
  '2026-05-01',
  '2026-05-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '新生通话',
  NULL,
  '2026-04-24',
  '2026-05-24',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-05',
  '上课数据',
  NULL,
  '2026-04-24',
  '2026-05-24',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '带生数',
  NULL,
  '2026-05-01',
  '2026-05-31',
  '2026春',
  '2026暑',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '课前退',
  NULL,
  '2026-05-18',
  '2026-06-23',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '试听退',
  NULL,
  '2026-05-16',
  '2026-06-15',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '课中退',
  NULL,
  '2026-06-01',
  '2026-06-30',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '学员回访',
  NULL,
  '2026-06-01',
  '2026-06-30',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '新生通话',
  NULL,
  '2026-05-25',
  '2026-06-23',
  '2026春,2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '上课数据',
  NULL,
  '2026-05-25',
  '2026-06-14',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-06',
  '作业数据',
  NULL,
  '2026-05-25',
  '2026-06-07',
  '2026春',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '带生数',
  NULL,
  '2026-08-01',
  '2026-08-31',
  '2026秋',
  '2026暑',
  '常规',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '课前退',
  NULL,
  '2026-05-18',
  '2026-06-23',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '试听退',
  NULL,
  '2026-05-18',
  '2026-08-15',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '课中退',
  NULL,
  '2026-08-01',
  '2026-08-31',
  '2026春,2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '学员回访',
  NULL,
  '2026-07-01',
  '2026-08-31',
  '',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '新生通话',
  NULL,
  '2026-05-18',
  '2026-08-24',
  '2026暑,2026秋',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

INSERT INTO bi.performance_configuration (
  create_by, update_by, create_date, update_date, config_month, module, content,
  time_start, time_end, period1, period2, config_type, del_flag
) VALUES (
  NULL,
  NULL,
  now(),
  now(),
  '2026-09',
  '上课数据',
  NULL,
  '2026-07-01',
  '2026-08-31',
  '2026暑',
  '',
  '',
  0
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
  config_type = EXCLUDED.config_type,
  del_flag = EXCLUDED.del_flag;

COMMIT;
