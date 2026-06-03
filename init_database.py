"""
数据库初始化脚本
创建source_db（模拟业务库）和dw_db（数据仓库）
"""

import mysql.connector
from mysql.connector import Error

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456'  # 请根据实际情况修改
}

SOURCE_DB = 'source_db'
DW_DB = 'dw_db'


def create_databases():
    """创建数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 创建源数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {SOURCE_DB}")
        print(f"数据库 {SOURCE_DB} 创建成功")

        # 创建数据仓库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DW_DB}")
        print(f"数据库 {DW_DB} 创建成功")

        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"创建数据库失败: {e}")
        return False


def create_source_tables():
    """创建源数据库表结构（含脏数据）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 用户表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SOURCE_DB}.users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                register_time DATETIME
            )
        """)
        print("  - 用户表创建成功")

        # 商品表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SOURCE_DB}.products (
                product_id INT PRIMARY KEY AUTO_INCREMENT,
                product_name VARCHAR(100) NOT NULL,
                category VARCHAR(50),
                price DECIMAL(10, 2),
                stock INT DEFAULT 0,
                create_time DATETIME
            )
        """)
        print("  - 商品表创建成功")

        # 订单表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SOURCE_DB}.orders (
                order_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                product_id INT,
                quantity INT,
                unit_price DECIMAL(10, 2),
                order_time DATETIME,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES {SOURCE_DB}.users(user_id),
                FOREIGN KEY (product_id) REFERENCES {SOURCE_DB}.products(product_id)
            )
        """)
        print("  - 订单表创建成功")

        # 日志表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SOURCE_DB}.logs (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                action VARCHAR(50),
                log_time DATETIME,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES {SOURCE_DB}.users(user_id)
            )
        """)
        print("  - 日志表创建成功")

        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"创建源表失败: {e}")
        return False


def create_dw_tables():
    """创建数据仓库表结构（星型模型）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 用户维度表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.dim_user (
                user_key INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                username VARCHAR(50),
                phone VARCHAR(20),
                email VARCHAR(100),
                register_time DATETIME,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_user_id (user_id)
            )
        """)
        print("  - 用户维度表创建成功")

        # 商品维度表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.dim_product (
                product_key INT PRIMARY KEY AUTO_INCREMENT,
                product_id INT NOT NULL,
                product_name VARCHAR(100),
                category VARCHAR(50),
                category_en VARCHAR(50),
                price DECIMAL(10, 2),
                stock INT,
                create_time DATETIME,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_product_id (product_id)
            )
        """)
        print("  - 商品维度表创建成功")

        # 日期维度表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.dim_date (
                date_key INT PRIMARY KEY AUTO_INCREMENT,
                date_value DATETIME NOT NULL,
                year INT,
                month INT,
                day INT,
                quarter INT,
                week_of_year INT,
                UNIQUE KEY uk_date_value (date_value)
            )
        """)
        print("  - 日期维度表创建成功")

        # 订单事实表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.fact_orders (
                order_key INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT NOT NULL,
                user_key INT,
                product_key INT,
                date_key INT,
                quantity INT,
                unit_price DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                status VARCHAR(20),
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_key) REFERENCES {DW_DB}.dim_user(user_key),
                FOREIGN KEY (product_key) REFERENCES {DW_DB}.dim_product(product_key),
                FOREIGN KEY (date_key) REFERENCES {DW_DB}.dim_date(date_key),
                UNIQUE KEY uk_order_id (order_id)
            )
        """)
        print("  - 订单事实表创建成功")

        # 日志事实表
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.fact_logs (
                log_key INT PRIMARY KEY AUTO_INCREMENT,
                log_id INT NOT NULL,
                user_id INT,
                action VARCHAR(50),
                log_time DATETIME,
                description TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_log_id (log_id)
            )
        """)
        print("  - 日志事实表创建成功")

        # ETL日志表（加分项：记录ETL运行状态）
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DW_DB}.etl_log (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                run_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                extracted_rows INT,
                transformed_rows INT,
                loaded_rows INT,
                error_rows INT,
                error_message TEXT
            )
        """)
        print("  - ETL日志表创建成功")

        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"创建数据仓库表失败: {e}")
        return False


def create_views():
    """创建视图（加分项）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 销售汇总视图
        cursor.execute(f"""
            CREATE OR REPLACE VIEW {DW_DB}.v_sales_summary AS
            SELECT
                d.year,
                d.quarter,
                d.month,
                p.category_en,
                COUNT(f.order_key) as order_count,
                SUM(f.quantity) as total_quantity,
                SUM(f.total_amount) as total_revenue
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_product p ON f.product_key = p.product_key
            JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
            GROUP BY d.year, d.quarter, d.month, p.category_en
        """)
        print("  - 销售汇总视图创建成功")

        # 用户购买行为视图
        cursor.execute(f"""
            CREATE OR REPLACE VIEW {DW_DB}.v_user_purchase AS
            SELECT
                u.user_id,
                u.username,
                COUNT(f.order_key) as order_count,
                SUM(f.total_amount) as total_spent
            FROM {DW_DB}.dim_user u
            LEFT JOIN {DW_DB}.fact_orders f ON u.user_key = f.user_key
            GROUP BY u.user_id, u.username
        """)
        print("  - 用户购买行为视图创建成功")

        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"创建视图失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("数据库初始化")
    print("=" * 50)

    # 创建数据库
    print("\n[1] 创建数据库...")
    if not create_databases():
        return

    # 创建源数据库表
    print("\n[2] 创建源数据库表...")
    if not create_source_tables():
        return

    # 创建数据仓库表
    print("\n[3] 创建数据仓库表（星型模型）...")
    if not create_dw_tables():
        return

    # 创建视图
    print("\n[4] 创建分析视图...")
    if not create_views():
        return

    print("\n" + "=" * 50)
    print("数据库初始化完成!")
    print("=" * 50)


if __name__ == '__main__':
    main()
