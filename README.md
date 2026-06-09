# 电商销售数据的 ETL 与多维分析系统

## 快速开始

### 1. 环境准备

```bash
# 创建conda环境
conda create -n .conda python=3.10
conda activate ./.conda

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

修改 `config.py` 中的数据库密码：

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password'  # 修改为你的密码
}
```

### 3. 运行

**方式一：一键运行（推荐）**
```bash
# 双击 run_all.bat 或在终端运行
.\run_all.bat
```

**方式二：分步运行**
```bash
# 初始化数据库
python init_database.py

# 生成测试数据
python generate_data.py

# 执行ETL
python etl_job.py

# 运行OLAP查询
python olap_queries.py

# 生成可视化图表
python olap_charts.py
```

---

## 模块简介

| 模块 | 说明 |
|------|------|
| `config.py` | 数据库配置（统一管理） |
| `init_database.py` | 初始化MySQL数据库，创建source_db和dw_db及所有表结构 |
| `generate_data.py` | 生成1000+条测试数据，包含故意设置的脏数据 |
| `etl_job.py` | ETL核心：抽取源数据 → 清洗转换 → 加载到数据仓库 |
| `olap_queries.py` | 10条OLAP多维分析查询，验证ETL效果 |
| `olap_charts.py` | 生成销售趋势可视化图表 |
| `run_all.bat` | 一键运行所有脚本 |
| `doc/draw_diagrams.py` | 绘制系统架构图和数据流图 |

---

## 数据流程

```
源数据库(source_db)
    ├── users      (用户表)
    ├── products   (商品表)
    ├── orders     (订单表)
    └── logs       (日志表)
           ↓ ETL
目标数据仓库(dw_db) - 星型模型
    ├── dim_user       (用户维度)
    ├── dim_product    (商品维度)
    ├── dim_date       (日期维度)
    ├── fact_orders    (订单事实)
    └── fact_logs      (日志事实)
```

---

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/olap_charts.png` | OLAP可视化图表 |
| `doc/architecture.png` | 系统架构图 |
| `doc/dataflow.png` | 数据流图 |
