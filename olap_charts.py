"""
OLAP可视化 - 生成销售趋势图表
"""

import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password'  # 修改为你的密码
}
DW_DB = 'dw_db'


def get_yearly_sales(cursor):
    """获取年度销售数据"""
    query = f"""
        SELECT d.year, SUM(f.total_amount) as revenue
        FROM {DW_DB}.fact_orders f
        JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
        GROUP BY d.year
        ORDER BY d.year
    """
    cursor.execute(query)
    return cursor.fetchall()


def get_monthly_sales(cursor, year):
    """获取月度销售数据"""
    query = f"""
        SELECT d.month, SUM(f.total_amount) as revenue
        FROM {DW_DB}.fact_orders f
        JOIN {DW_DB}.dim_date d ON f.date_key = d.date_key
        WHERE d.year = {year}
        GROUP BY d.month
        ORDER BY d.month
    """
    cursor.execute(query)
    return cursor.fetchall()


def get_category_sales(cursor):
    """获取分类销售数据"""
    query = f"""
        SELECT p.category_en, SUM(f.total_amount) as revenue
        FROM {DW_DB}.fact_orders f
        JOIN {DW_DB}.dim_product p ON f.product_key = p.product_key
        GROUP BY p.category_en
        ORDER BY revenue DESC
    """
    cursor.execute(query)
    return cursor.fetchall()


def get_order_status(cursor):
    """获取订单状态分布"""
    query = f"""
        SELECT status, COUNT(*) as count
        FROM {DW_DB}.fact_orders
        GROUP BY status
    """
    cursor.execute(query)
    return cursor.fetchall()


def plot_charts():
    """绘制所有图表"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('电商销售数据 OLAP 可视化分析', fontsize=16)

        # 1. 年度销售趋势
        yearly = get_yearly_sales(cursor)
        if yearly:
            years = [str(r[0]) for r in yearly]
            revenues = [r[1] for r in yearly]
            axes[0, 0].bar(years, revenues, color='steelblue')
            axes[0, 0].set_title('年度销售额趋势')
            axes[0, 0].set_xlabel('年份')
            axes[0, 0].set_ylabel('销售额')
            for i, v in enumerate(revenues):
                axes[0, 0].text(i, v, f'{v:.0f}', ha='center')

        # 2. 月度销售趋势（当年）
        monthly = get_monthly_sales(cursor, 2026)
        if monthly:
            months = [f'{r[0]}月' for r in monthly]
            revenues = [r[1] for r in monthly]
            axes[0, 1].plot(months, revenues, marker='o', linewidth=2, color='coral')
            axes[0, 1].set_title('2026年月度销售额趋势')
            axes[0, 1].set_xlabel('月份')
            axes[0, 1].set_ylabel('销售额')
            axes[0, 1].grid(True, linestyle='--', alpha=0.7)

        # 3. 分类销售占比
        category = get_category_sales(cursor)
        if category:
            categories = [r[0] for r in category]
            revenues = [r[1] for r in category]
            colors = plt.cm.Set3(range(len(categories)))
            axes[1, 0].pie(revenues, labels=categories, autopct='%1.1f%%', colors=colors)
            axes[1, 0].set_title('商品分类销售占比')

        # 4. 订单状态分布
        status = get_order_status(cursor)
        if status:
            statuses = [r[0] for r in status]
            counts = [r[1] for r in status]
            colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999']
            axes[1, 1].bar(statuses, counts, color=colors[:len(statuses)])
            axes[1, 1].set_title('订单状态分布')
            axes[1, 1].set_xlabel('状态')
            axes[1, 1].set_ylabel('订单数')
            for i, v in enumerate(counts):
                axes[1, 1].text(i, v, str(v), ha='center')

        plt.tight_layout()
        plt.savefig('olap_charts.png', dpi=150, bbox_inches='tight')
        print('图表已保存至 olap_charts.png')

        cursor.close()
        conn.close()

    except Error as e:
        print(f'数据库错误: {e}')


if __name__ == '__main__':
    plot_charts()
