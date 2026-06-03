"""
主程序 - ETL与多维分析系统运行器
按顺序执行所有步骤
"""

import sys


def main():
    """主函数"""
    print("=" * 60)
    print("电商销售数据的 ETL 与多维分析系统")
    print("=" * 60)

    print("\n使用说明:")
    print("1. 首先修改各脚本中的数据库密码")
    print("2. 运行 init_database.py 初始化数据库")
    print("3. 运行 generate_data.py 生成测试数据")
    print("4. 运行 etl_job.py 执行ETL")
    print("5. 运行 olap_queries.py 查看分析结果")
    print("6. 查看 report_template.md 撰写报告")

    print("\n" + "=" * 60)
    print("快速开始")
    print("=" * 60)

    print("\n1. 初始化数据库...")
    print("   python init_database.py")

    print("\n2. 生成测试数据...")
    print("   python generate_data.py")

    print("\n3. 执行ETL...")
    print("   python etl_job.py")

    print("\n4. 运行OLAP查询...")
    print("   python olap_queries.py")


if __name__ == '__main__':
    main()
