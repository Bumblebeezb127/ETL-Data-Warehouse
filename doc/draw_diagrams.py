"""
绘制ETL系统架构图和数据流图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib
matplotlib.use('Agg')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def draw_architecture_diagram():
    """绘制系统架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('电商销售数据ETL系统架构图', fontsize=18, fontweight='bold', pad=20)

    # 颜色定义
    source_color = '#FFE4B5'
    dw_color = '#B0E0E6'
    etl_color = '#98FB98'
    arrow_color = '#666666'

    # 1. 源数据库 (左侧)
    source_box = FancyBboxPatch((0.5, 3), 3, 5, boxstyle="round,pad=0.1",
                                  facecolor=source_color, edgecolor='black', linewidth=2)
    ax.add_patch(source_box)
    ax.text(2, 7.5, 'source_db', fontsize=14, ha='center', fontweight='bold')
    ax.text(2, 6.5, '源数据库', fontsize=10, ha='center')

    tables = ['users', 'products', 'orders', 'logs']
    for i, table in enumerate(tables):
        ax.text(2, 5.5 - i * 0.6, f'- {table}', fontsize=10, ha='center')

    # 2. ETL处理 (中间)
    etl_box = FancyBboxPatch((5, 2.5), 4, 6, boxstyle="round,pad=0.1",
                               facecolor=etl_color, edgecolor='black', linewidth=2)
    ax.add_patch(etl_box)
    ax.text(7, 8, 'ETL Job', fontsize=14, ha='center', fontweight='bold')
    ax.text(7, 7.2, 'etl_job.py', fontsize=10, ha='center', style='italic')

    steps = ['抽取 Extract', '清洗 Clean', '转换 Transform', '加载 Load']
    colors = ['#87CEEB', '#FFD700', '#FF69B4', '#32CD32']
    for i, step in enumerate(steps):
        ax.add_patch(FancyBboxPatch((5.3, 5.8 - i * 1.3), 3.4, 0.9,
                                    boxstyle="round,pad=0.05",
                                    facecolor=colors[i], edgecolor='gray'))
        ax.text(7, 6.25 - i * 1.3, step, fontsize=10, ha='center', va='center')

    # 3. 数据仓库 (右侧)
    dw_box = FancyBboxPatch((10.5, 1.5), 3, 7.5, boxstyle="round,pad=0.1",
                             facecolor=dw_color, edgecolor='black', linewidth=2)
    ax.add_patch(dw_box)
    ax.text(12, 8.5, 'dw_db', fontsize=14, ha='center', fontweight='bold')
    ax.text(12, 7.8, '数据仓库', fontsize=10, ha='center')
    ax.text(12, 7.3, '(星型模型)', fontsize=9, ha='center', style='italic')

    ax.text(11.8, 6.5, '维度表:', fontsize=10, fontweight='bold', va='top')
    dims = ['dim_user', 'dim_product', 'dim_date']
    for i, dim in enumerate(dims):
        ax.text(11.8, 6 - i * 0.6, f'- {dim}', fontsize=9, ha='center')

    ax.text(11.8, 4.2, '事实表:', fontsize=10, fontweight='bold', va='top')
    facts = ['fact_orders', 'fact_logs']
    for i, fact in enumerate(facts):
        ax.text(11.8, 3.6 - i * 0.6, f'- {fact}', fontsize=9, ha='center')

    # 箭头
    ax.annotate('', xy=(5, 5), xytext=(3.5, 5),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.text(4.25, 5.3, '抽取', fontsize=9)

    ax.annotate('', xy=(10.5, 5), xytext=(9, 5),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2))
    ax.text(9.5, 5.3, '加载', fontsize=9)

    # 4. OLAP查询 (下方)
    olap_box = FancyBboxPatch((5, 0.2), 4, 1.5, boxstyle="round,pad=0.1",
                               facecolor='#E6E6FA', edgecolor='black', linewidth=2)
    ax.add_patch(olap_box)
    ax.text(7, 1.2, 'OLAP 分析查询', fontsize=11, ha='center', fontweight='bold')
    ax.text(7, 0.6, 'olap_queries.py / olap_charts.py', fontsize=9, ha='center', style='italic')

    ax.annotate('', xy=(7, 1.5), xytext=(7, 1.5),
                arrowprops=dict(arrowstyle='->', color=arrow_color, lw=2,
                               connectionstyle='arc3,rad=0.3'))

    # 图例
    legend_elements = [
        mpatches.Patch(facecolor=source_color, edgecolor='black', label='源数据库 (source_db)'),
        mpatches.Patch(facecolor=etl_color, edgecolor='black', label='ETL处理'),
        mpatches.Patch(facecolor=dw_color, edgecolor='black', label='数据仓库 (dw_db)'),
        mpatches.Patch(facecolor='#E6E6FA', edgecolor='black', label='OLAP分析'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    plt.tight_layout()
    plt.savefig('doc/architecture.png', dpi=150, bbox_inches='tight')
    print('架构图已保存至 doc/architecture.png')
    plt.close()


def draw_dataflow_diagram():
    """绘制数据流图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    ax.set_title('电商销售数据ETL数据流图', fontsize=18, fontweight='bold', pad=20)

    node_colors = {
        'source': '#FFE4B5',
        'process': '#98FB98',
        'transform': '#FFB6C1',
        'dw': '#B0E0E6',
        'output': '#E6E6FA'
    }

    # ===== 左侧：源数据层 =====
    ax.add_patch(FancyBboxPatch((0.5, 9), 3, 1.2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['source'], edgecolor='black'))
    ax.text(2, 9.6, 'users', fontsize=11, ha='center', fontweight='bold')

    ax.add_patch(FancyBboxPatch((0.5, 7), 3, 1.2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['source'], edgecolor='black'))
    ax.text(2, 7.6, 'products', fontsize=11, ha='center', fontweight='bold')

    ax.add_patch(FancyBboxPatch((0.5, 5), 3, 1.2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['source'], edgecolor='black'))
    ax.text(2, 5.6, 'orders', fontsize=11, ha='center', fontweight='bold')

    ax.add_patch(FancyBboxPatch((0.5, 3), 3, 1.2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['source'], edgecolor='black'))
    ax.text(2, 3.6, 'logs', fontsize=11, ha='center', fontweight='bold')

    # ===== 中间：ETL处理层 =====
    ax.add_patch(FancyBboxPatch((5, 8.5), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['process'], edgecolor='black', linewidth=2))
    ax.text(6.5, 9.8, '抽取 Extract', fontsize=11, ha='center', fontweight='bold')
    ax.text(6.5, 9.3, '读取原始数据', fontsize=9, ha='center')
    ax.text(6.5, 8.8, 'etl_job.py', fontsize=8, ha='center', style='italic')

    ax.add_patch(FancyBboxPatch((5, 5.5), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['transform'], edgecolor='black', linewidth=2))
    ax.text(6.5, 6.8, '清洗 Clean', fontsize=11, ha='center', fontweight='bold')
    ax.text(6.5, 6.3, '数据质量校验', fontsize=9, ha='center')
    ax.text(6.5, 5.8, '过滤脏数据', fontsize=9, ha='center')

    ax.add_patch(FancyBboxPatch((5, 2.5), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['transform'], edgecolor='black', linewidth=2))
    ax.text(6.5, 3.8, '转换 Transform', fontsize=11, ha='center', fontweight='bold')
    ax.text(6.5, 3.3, '格式统一', fontsize=9, ha='center')
    ax.text(6.5, 2.8, '分类映射', fontsize=9, ha='center')

    ax.add_patch(FancyBboxPatch((9.5, 5.5), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['process'], edgecolor='black', linewidth=2))
    ax.text(11, 6.8, '加载 Load', fontsize=11, ha='center', fontweight='bold')
    ax.text(11, 6.3, 'UPSERT策略', fontsize=9, ha='center')
    ax.text(11, 5.8, '维度+事实表', fontsize=9, ha='center')

    # ===== 右侧：数据仓库层 =====
    ax.add_patch(FancyBboxPatch((14, 7.5), 1.5, 3.5, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['dw'], edgecolor='black'))
    ax.text(14.75, 10.5, 'dim_user', fontsize=9, ha='center', fontweight='bold')
    ax.text(14.75, 9.5, 'dim_product', fontsize=9, ha='center', fontweight='bold')
    ax.text(14.75, 8.5, 'dim_date', fontsize=9, ha='center', fontweight='bold')
    ax.text(14.75, 7.8, '维度表', fontsize=10, ha='center')

    ax.add_patch(FancyBboxPatch((14, 4), 1.5, 2.5, boxstyle="round,pad=0.1",
                                 facecolor=node_colors['dw'], edgecolor='black'))
    ax.text(14.75, 6, 'fact_orders', fontsize=9, ha='center', fontweight='bold')
    ax.text(14.75, 5, 'fact_logs', fontsize=9, ha='center', fontweight='bold')
    ax.text(14.75, 4.3, '事实表', fontsize=10, ha='center')

    # ===== 箭头 =====
    arrow_style = dict(arrowstyle='->', color='#333333', lw=1.5)

    ax.annotate('', xy=(5, 9.5), xytext=(3.5, 9.5), arrowprops=arrow_style)
    ax.annotate('', xy=(5, 7.5), xytext=(3.5, 7.5), arrowprops=arrow_style)
    ax.annotate('', xy=(5, 5.5), xytext=(3.5, 5.5), arrowprops=arrow_style)
    ax.annotate('', xy=(5, 3.5), xytext=(3.5, 3.5), arrowprops=arrow_style)

    ax.annotate('', xy=(6.5, 7.5), xytext=(6.5, 8.5), arrowprops=arrow_style)
    ax.annotate('', xy=(6.5, 4.5), xytext=(6.5, 5.5), arrowprops=arrow_style)
    ax.annotate('', xy=(9.5, 6.5), xytext=(8, 4.5), arrowprops=arrow_style)
    ax.annotate('', xy=(14, 8.5), xytext=(12.5, 6.5), arrowprops=arrow_style)
    ax.annotate('', xy=(14, 5.5), xytext=(12.5, 6.5), arrowprops=arrow_style)

    # ===== 清洗规则说明框 =====
    rules_text = """清洗规则:
- 手机号: 正则 ^1[3-9]\\d{9}$
- 价格: > 0
- 日期: YYYY-MM-DD HH:MM:SS
- 空值: 必填字段不能为空"""

    ax.text(0.5, 1.5, rules_text, fontsize=9, va='top',
            bbox=dict(boxstyle='round', facecolor='#FFFACD', edgecolor='gray'))

    # ===== 转换规则说明框 =====
    transform_text = """转换规则:
- 分类映射: 手机->Electronics
- 日期拆解: 年/月/日/季度/周
- 金额计算: quantity x price"""

    ax.text(5, 1.5, transform_text, fontsize=9, va='top',
            bbox=dict(boxstyle='round', facecolor='#FFE4E1', edgecolor='gray'))

    # ===== 输出说明框 =====
    output_text = """输出:
- 维度表: dim_user, dim_product, dim_date
- 事实表: fact_orders, fact_logs
- 分析: olap_queries.py
- 可视化: olap_charts.py"""

    ax.text(9.5, 1.5, output_text, fontsize=9, va='top',
            bbox=dict(boxstyle='round', facecolor='#E6E6FA', edgecolor='gray'))

    plt.tight_layout()
    plt.savefig('doc/dataflow.png', dpi=150, bbox_inches='tight')
    print('数据流图已保存至 doc/dataflow.png')
    plt.close()


def main():
    print("正在绘制架构图和数据流图...")
    draw_architecture_diagram()
    draw_dataflow_diagram()
    print("完成!")


if __name__ == '__main__':
    main()
