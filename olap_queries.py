"""
OLAP分析查询 - 验证ETL效果
在dw_db上执行多维分析查询
"""

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG, DW_DB

DB_CONFIG['database'] = DW_DB


def execute_query(cursor, query_name, query):
    """执行查询并打印结果"""
    print(f"\n{'=' * 60}")
    print(f"【{query_name}】")
    print('=' * 60)
    print(f"SQL: {query}\n")

    try:
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("结果: 无数据")
            return

        # 打印列名
        columns = cursor.column_names
        print(f"{' | '.join(str(col) for col in columns)}")
        print('-' * 60)

        # 打印数据（限制前20行）
        for i, row in enumerate(results[:20]):
            print(' | '.join(str(val) for val in row))

        if len(results) > 20:
            print(f"... (共 {len(results)} 行)")

        print(f"\n共 {len(results)} 行结果")

    except Error as e:
        print(f"查询失败: {e}")


def run_olap_queries():
    """运行所有OLAP查询"""
    print("=" * 60)
    print("OLAP 多维分析查询")
    print("=" * 60)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 查询1: 各年度销售额趋势
        execute_query(cursor, "1. 年度销售趋势", f"""
            SELECT
                d.year AS 年份,
                COUNT(f.order_key) AS 订单数,
                SUM(f.quantity) AS 总销量,
                SUM(f.total_amount) AS 总销售额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
            GROUP BY d.year
            ORDER BY d.year
        """)

        # 查询2: 各季度销售对比
        execute_query(cursor, "2. 季度销售对比", f"""
            SELECT
                d.year AS 年份,
                d.quarter AS 季度,
                p.category_en AS 分类,
                COUNT(f.order_key) AS 订单数,
                SUM(f.total_amount) AS 销售额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
            JOIN {DW_DB}.dim_product p ON f.product_key = p.product_key
            GROUP BY d.year, d.quarter, p.category_en
            ORDER BY d.year, d.quarter, 销售额 DESC
        """)

        # 查询3: 月度销售趋势（当年）
        execute_query(cursor, "3. 月度销售趋势", f"""
            SELECT
                d.month AS 月份,
                COUNT(f.order_key) AS 订单数,
                SUM(f.quantity) AS 总销量,
                SUM(f.total_amount) AS 总销售额,
                ROUND(AVG(f.total_amount), 2) AS 平均订单金额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
            WHERE d.year = YEAR(CURRENT_DATE)
            GROUP BY d.month
            ORDER BY d.month
        """)

        # 查询4: 商品分类销售排行
        execute_query(cursor, "4. 商品分类销售排行", f"""
            SELECT
                p.category_en AS 分类,
                COUNT(DISTINCT p.product_id) AS 商品数,
                COUNT(f.order_key) AS 订单数,
                SUM(f.quantity) AS 总销量,
                SUM(f.total_amount) AS 总销售额,
                ROUND(AVG(f.total_amount), 2) AS 平均订单金额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_product p ON f.product_key = p.product_key
            GROUP BY p.category_en
            ORDER BY 总销售额 DESC
        """)

        # 查询5: 高价值用户分析
        execute_query(cursor, "5. 高价值用户分析 (Top 20)", f"""
            SELECT
                u.user_id AS 用户ID,
                u.username AS 用户名,
                COUNT(f.order_key) AS 订单数,
                SUM(f.quantity) AS 总购买数量,
                SUM(f.total_amount) AS 总消费金额,
                ROUND(AVG(f.total_amount), 2) AS 平均订单金额
            FROM {DW_DB}.dim_user u
            LEFT JOIN {DW_DB}.fact_orders f ON u.user_key = f.user_key
            GROUP BY u.user_id, u.username
            HAVING 总消费金额 > 0
            ORDER BY 总消费金额 DESC
            LIMIT 20
        """)

        # 查询6: 订单状态分布
        execute_query(cursor, "6. 订单状态分布", f"""
            SELECT
                f.status AS 订单状态,
                COUNT(f.order_key) AS 订单数,
                SUM(f.total_amount) AS 总销售额,
                ROUND(COUNT(f.order_key) * 100.0 / (SELECT COUNT(*) FROM {DW_DB}.fact_orders), 2) AS 占比
            FROM {DW_DB}.fact_orders f
            GROUP BY f.status
            ORDER BY 订单数 DESC
        """)

        # 查询7: 用户行为分析
        execute_query(cursor, "7. 用户行为分析", f"""
            SELECT
                action AS 行为类型,
                COUNT(*) AS 行为次数,
                COUNT(DISTINCT user_id) AS 涉及用户数
            FROM {DW_DB}.fact_logs
            GROUP BY action
            ORDER BY 行为次数 DESC
        """)

        # 查询8: 周销售情况
        execute_query(cursor, "8. 周销售情况", f"""
            SELECT
                d.year AS 年份,
                d.week_of_year AS 周数,
                COUNT(f.order_key) AS 订单数,
                SUM(f.total_amount) AS 周销售额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
            GROUP BY d.year, d.week_of_year
            ORDER BY d.year, d.week_of_year
            LIMIT 20
        """)

        # 查询9: 商品销售排行榜
        execute_query(cursor, "9. 商品销售排行榜 (Top 10)", f"""
            SELECT
                p.product_id AS 商品ID,
                p.product_name AS 商品名称,
                p.category_en AS 分类,
                COUNT(f.order_key) AS 销售次数,
                SUM(f.quantity) AS 总销量,
                SUM(f.total_amount) AS 总销售额
            FROM {DW_DB}.fact_orders f
            JOIN {DW_DB}.dim_product p ON f.product_key = p.product_key
            GROUP BY p.product_id, p.product_name, p.category_en
            ORDER BY 总销售额 DESC
            LIMIT 10
        """)

        # 查询10: 用户购买频次分析
        execute_query(cursor, "10. 用户购买频次分析", f"""
            SELECT
                order_count AS 购买次数,
                COUNT(*) AS 用户数,
                SUM(total_spent) AS 总消费
            FROM (
                SELECT
                    u.user_id,
                    COUNT(f.order_key) as order_count,
                    COALESCE(SUM(f.total_amount), 0) as total_spent
                FROM {DW_DB}.dim_user u
                LEFT JOIN {DW_DB}.fact_orders f ON u.user_key = f.user_key
                GROUP BY u.user_id
            ) t
            GROUP BY order_count
            ORDER BY order_count
            LIMIT 15
        """)

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("OLAP查询全部完成!")
        print("=" * 60)

    except Error as e:
        print(f"数据库错误: {e}")


def main():
    """主函数"""
    run_olap_queries()


if __name__ == '__main__':
    main()
