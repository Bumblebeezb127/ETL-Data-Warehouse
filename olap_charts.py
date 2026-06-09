"""
OLAP可视化 - 生成销售趋势图表
"""

import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.font_manager import FontProperties
from config import DB_CONFIG, DW_DB
import os

DB_CONFIG['database'] = DW_DB

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


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
        fig.suptitle('电商销售数据OLAP分析', fontsize=18, fontweight='bold', y=1.02)

        # 1. 年度销售趋势
        yearly = get_yearly_sales(cursor)
        if yearly:
            years = [str(r[0]) for r in yearly]
            revenues = [r[1] for r in yearly]
            axes[0, 0].bar(years, revenues, color='steelblue')
            axes[0, 0].set_title('年度销售额趋势', fontsize=14, fontweight='bold')
            axes[0, 0].set_xlabel('年份', fontsize=12)
            axes[0, 0].set_ylabel('销售额', fontsize=12)
            for i, v in enumerate(revenues):
                axes[0, 0].text(i, v, f'{v:.0f}', ha='center')

        # 2. 月度销售趋势（当年）
        monthly = get_monthly_sales(cursor, 2026)
        if monthly:
            months = [f'{r[0]}月' for r in monthly]
            revenues = [r[1] for r in monthly]
            axes[0, 1].plot(months, revenues, marker='o', linewidth=2, color='coral')
            axes[0, 1].set_title('2026年月度销售额趋势', fontsize=14, fontweight='bold')
            axes[0, 1].set_xlabel('月份', fontsize=12)
            axes[0, 1].set_ylabel('销售额', fontsize=12)
            axes[0, 1].grid(True, linestyle='--', alpha=0.7)

        # 3. 分类销售占比
        category = get_category_sales(cursor)
        if category:
            categories = [r[0] for r in category]
            revenues = [r[1] for r in category]
            colors = plt.cm.Set3(range(len(categories)))
            axes[1, 0].pie(revenues, labels=categories, autopct='%1.1f%%', colors=colors)
            axes[1, 0].set_title('商品分类销售占比', fontsize=14, fontweight='bold')

        # 4. 订单状态分布
        status = get_order_status(cursor)
        if status:
            # 状态中文映射
            status_map = {'pending': '待支付', 'paid': '已支付', 'shipped': '已发货', 'completed': '已完成', 'cancelled': '已取消'}
            statuses = [status_map.get(r[0], r[0]) for r in status]
            counts = [r[1] for r in status]
            colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999', '#cccccc']
            axes[1, 1].bar(statuses, counts, color=colors[:len(statuses)])
            axes[1, 1].set_title('订单状态分布', fontsize=14, fontweight='bold')
            axes[1, 1].set_xlabel('状态', fontsize=12)
            axes[1, 1].set_ylabel('数量', fontsize=12)
            for i, v in enumerate(counts):
                axes[1, 1].text(i, v, str(v), ha='center')

        plt.tight_layout()
        plt.savefig('output/olap_charts.png', dpi=150, bbox_inches='tight')
        print('Charts saved to output/olap_charts.png')

        cursor.close()
        conn.close()

    except Error as e:
        print(f'Database error: {e}')


if __name__ == '__main__':
    plot_charts()
