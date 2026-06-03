# 电商销售数据的 ETL 与多维分析系统 - 项目报告模板

## 一、项目概述

### 1.1 项目背景
描述为什么选择这个题目，项目要解决什么问题。

### 1.2 项目目标
- 从多个模拟业务源表抽取数据
- 清洗转换后加载到星型模型数据仓库
- 支持基础 OLAP 查询

---

## 二、系统架构

### 2.1 架构图
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  source_db  │ ──> │   ETL脚本   │ ──> │    dw_db    │
│  (业务库)   │     │  etl_job.py │     │  (数据仓库) │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ OLAP查询    │
                                        └─────────────┘
```

### 2.2 技术栈
- 数据库: MySQL
- 开发语言: Python
- 主要库: mysql-connector-python

---

## 三、源数据设计（含脏数据）

### 3.1 源表结构

#### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | INT | 用户ID |
| username | VARCHAR | 用户名 |
| phone | VARCHAR | 手机号 |
| email | VARCHAR | 邮箱 |
| register_time | DATETIME | 注册时间 |

#### 商品表 (products)
| 字段 | 类型 | 说明 |
|------|------|------|
| product_id | INT | 商品ID |
| product_name | VARCHAR | 商品名称 |
| category | VARCHAR | 分类 |
| price | DECIMAL | 价格 |
| stock | INT | 库存 |
| create_time | DATETIME | 创建时间 |

#### 订单表 (orders)
| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | INT | 订单ID |
| user_id | INT | 用户ID |
| product_id | INT | 商品ID |
| quantity | INT | 数量 |
| unit_price | DECIMAL | 单价 |
| order_time | DATETIME | 订单时间 |
| status | VARCHAR | 状态 |

#### 日志表 (logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| log_id | INT | 日志ID |
| user_id | INT | 用户ID |
| action | VARCHAR | 行为 |
| log_time | DATETIME | 时间 |
| description | TEXT | 描述 |

### 3.2 脏数据类型
- **无效手机号**: 长度错误、前缀错误、包含字母、空值
- **无效价格**: 负数、零、空值、价格过高
- **无效日期**: 格式混乱（/、-、无分隔符）、未来日期、空值

---

## 四、数据仓库设计（星型模型）

### 4.1 维度表

#### dim_user (用户维度)
| 字段 | 类型 | 说明 |
|------|------|------|
| user_key | INT | 代理键 |
| user_id | INT | 用户ID |
| username | VARCHAR | 用户名 |
| phone | VARCHAR | 手机号 |
| email | VARCHAR | 邮箱 |
| register_time | DATETIME | 注册时间 |

#### dim_product (商品维度)
| 字段 | 类型 | 说明 |
|------|------|------|
| product_key | INT | 代理键 |
| product_id | INT | 商品ID |
| product_name | VARCHAR | 商品名称 |
| category | VARCHAR | 原分类 |
| category_en | VARCHAR | 英文分类 |
| price | DECIMAL | 价格 |
| stock | INT | 库存 |

#### dim_date (日期维度)
| 字段 | 类型 | 说明 |
|------|------|------|
| date_key | INT | 代理键 |
| date_value | DATETIME | 日期值 |
| year | INT | 年 |
| month | INT | 月 |
| day | INT | 日 |
| quarter | INT | 季度 |
| week_of_year | INT | 年中第几周 |

### 4.2 事实表

#### fact_orders (订单事实表)
| 字段 | 类型 | 说明 |
|------|------|------|
| order_key | INT | 代理键 |
| order_id | INT | 订单ID |
| user_key | INT | 用户外键 |
| product_key | INT | 商品外键 |
| date_key | INT | 日期外键 |
| quantity | INT | 数量 |
| unit_price | DECIMAL | 单价 |
| total_amount | DECIMAL | 总金额 |
| status | VARCHAR | 状态 |

#### fact_logs (日志事实表)
| 字段 | 类型 | 说明 |
|------|------|------|
| log_key | INT | 代理键 |
| log_id | INT | 日志ID |
| user_id | INT | 用户ID |
| action | VARCHAR | 行为 |
| log_time | DATETIME | 时间 |
| description | TEXT | 描述 |

---

## 五、ETL流程

### 5.1 抽取（Extract）
从 source_db 的四张原始表读取数据。

### 5.2 清洗转换（Transform）

#### 数据清洗规则

| 规则 | 处理方式 |
|------|----------|
| 手机号校验 | 正则表达式 `^1[3-9]\d{9}$`，不符合则过滤 |
| 价格校验 | 必须 > 0，否则过滤 |
| 日期格式 | 统一转换为 `YYYY-MM-DD HH:MM:SS` |
| 空值处理 | 必填字段为空则过滤该记录 |

#### 数据转换规则

| 转换项 | 规则 |
|--------|------|
| 商品分类 | 手机→Electronics，书籍→Books... |
| 日期维度 | 从订单时间拆解年/月/日/季度/周 |
| 总金额 | quantity × unit_price |

### 5.3 加载（Load）
- 使用 UPSERT 策略（存在则更新，否则插入）
- 先加载维度表，再加载事实表
- 保证外键引用完整性

---

## 六、OLAP分析结果

### 6.1 查询示例

#### 查询1: 年度销售趋势
```sql
SELECT d.year, COUNT(*), SUM(f.total_amount)
FROM fact_orders f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year
```

#### 查询2: 分类销售排行
```sql
SELECT p.category_en, SUM(f.total_amount)
FROM fact_orders f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category_en
ORDER BY SUM(f.total_amount) DESC
```

### 6.2 分析结果截图
[在此处插入截图]

---

## 七、遇到的问题与解决方案

### 问题1: 主外键冲突
**问题描述**: 事实表加载时外键引用不存在
**解决方案**: 确保维度表先加载，使用事务保证完整性

### 问题2: 日期格式不一致
**问题描述**: 源数据中日期格式混乱
**解决方案**: 实现多种格式自动识别，优先使用正则解析

---

## 八、项目文件清单

| 文件 | 说明 |
|------|------|
| init_database.py | 数据库初始化脚本 |
| generate_data.py | 测试数据生成脚本 |
| etl_job.py | ETL核心脚本 |
| olap_queries.py | OLAP分析查询 |
| run.py | 运行器 |

---

## 九、总结与展望

### 9.1 完成情况
- [x] 任务1: 构建模拟源数据
- [x] 任务2: 设计数据仓库模型
- [x] 任务3: 实现ETL脚本
- [x] 任务4: OLAP分析查询
- [x] 任务5: 撰写报告

### 9.2 加分项实现
- [ ] 增量抽取（通过 last_update_time）
- [x] ETL日志表
- [x] 视图封装常用查询
- [ ] Matplotlib销售趋势图
- [ ] 缓慢变化维Type 2

### 9.3 改进建议
1. 实现增量ETL，提高处理效率
2. 添加数据质量监控
3. 优化查询性能，添加适当索引
