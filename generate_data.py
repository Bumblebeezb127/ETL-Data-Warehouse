"""
数据生成脚本 - 生成1000+条测试数据
包含"脏数据"用于测试ETL的数据清洗能力
"""

import random
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import logging
from config import DB_CONFIG, SOURCE_DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG['database'] = SOURCE_DB

# 数据配置
CATEGORIES = ['手机', '电脑', '书籍', '服装', '食品', '家具', '玩具', '平板']
CATEGORY_PRODUCTS = {
    '手机': ['iPhone', '小米手机', '华为手机', 'OPPO手机', 'vivo手机'],
    '电脑': ['联想电脑', '戴尔电脑', '惠普电脑', '苹果电脑', '华硕电脑'],
    '书籍': ['Python编程', '数据结构', '算法导论', '数据库原理', '设计模式'],
    '服装': ['T恤', '牛仔裤', '连衣裙', '外套', '运动裤'],
    '食品': ['零食', '饮料', '巧克力', '咖啡', '水果'],
    '家具': ['椅子', '桌子', '床', '衣柜', '沙发'],
    '玩具': ['积木', '遥控车', '玩偶', '拼图', '球类'],
    '平板': ['iPad', '小米平板', '华为平板', '联想平板', 'surface']
}

ACTIONS = ['login', 'logout', 'browse', 'cart', 'purchase', 'refund', 'search']
STATUSES = ['pending', 'completed', 'cancelled', 'shipped']


def generate_dirty_phone():
    """
    生成手机号，包含无效手机号（脏数据）
    """
    dirty_type = random.choice(['valid', 'invalid_length', 'invalid_prefix', 'empty', 'format_error'])

    if dirty_type == 'valid':
        # 有效手机号：1开头，11位
        prefix = random.choice(['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                               '150', '151', '152', '153', '155', '156', '157', '158', '159',
                               '170', '171', '172', '173', '175', '176', '177', '178',
                               '180', '181', '182', '183', '184', '185', '186', '187', '188', '189'])
        return prefix + ''.join([str(random.randint(0, 9)) for _ in range(8)])

    elif dirty_type == 'invalid_length':
        # 长度不对
        length = random.choice([8, 10, 12, 13])
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    elif dirty_type == 'invalid_prefix':
        # 1开头但第二位不对
        return '2' + ''.join([str(random.randint(0, 9)) for _ in range(10)])

    elif dirty_type == 'empty':
        return ''

    else:  # format_error
        # 格式错误，包含字母
        return ''.join([random.choice('0123456789ABCDEF') for _ in range(11)])


def generate_dirty_price():
    """
    生成价格，包含无效价格（脏数据）
    """
    dirty_type = random.choice(['valid', 'negative', 'zero', 'null', 'too_high'])

    if dirty_type == 'valid':
        return round(random.uniform(10, 5000), 2)

    elif dirty_type == 'negative':
        return round(random.uniform(-1000, -1), 2)

    elif dirty_type == 'zero':
        return 0

    elif dirty_type == 'null':
        return None

    else:  # too_high
        return round(random.uniform(1000000, 9999999), 2)


def generate_dirty_date():
    """
    生成日期，包含无效日期（脏数据）
    注意：只生成逻辑上无效的日期，格式必须是有效的MySQL日期格式
    逻辑无效类型：未来日期、空值
    """
    dirty_type = random.choice(['valid', 'future', 'null'])

    # 随机日期（在过去一年内）
    days_ago = random.randint(0, 365)
    date = datetime.now() - timedelta(days=days_ago)

    if dirty_type == 'valid':
        return date.strftime('%Y-%m-%d %H:%M:%S')

    elif dirty_type == 'future':
        # 未来日期（逻辑上无效）
        future_date = datetime.now() + timedelta(days=random.randint(1, 365))
        return future_date.strftime('%Y-%m-%d %H:%M:%S')

    else:  # null
        return None


def generate_data(cursor):
    """生成并插入测试数据"""
    logger.info("开始生成测试数据...")

    # 清空现有数据
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DELETE FROM logs")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM users")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    logger.info("已清空现有数据")

    # 生成用户数据
    logger.info("生成用户数据...")
    user_ids = []
    for i in range(500):
        user_id = i + 1
        username = f"user_{user_id:04d}"
        phone = generate_dirty_phone()
        email = f"user{user_id}@example.com" if random.random() > 0.1 else None
        register_time = generate_dirty_date()

        if register_time and email is not None:  # 过滤完全无效的数据
            cursor.execute(
                "INSERT INTO users (user_id, username, phone, email, register_time) VALUES (%s, %s, %s, %s, %s)",
                (user_id, username, phone, email, register_time)
            )
            user_ids.append(user_id)

    logger.info(f"生成 {len(user_ids)} 个用户")

    # 生成商品数据
    logger.info("生成商品数据...")
    product_ids = []
    for i in range(200):
        product_id = i + 1
        category = random.choice(CATEGORIES)
        product_name = random.choice(CATEGORY_PRODUCTS[category]) + f"_{product_id}"
        price = generate_dirty_price()
        stock = random.randint(0, 1000)
        create_time = generate_dirty_date()

        if price is not None and price > 0 and create_time:
            cursor.execute(
                "INSERT INTO products (product_id, product_name, category, price, stock, create_time) VALUES (%s, %s, %s, %s, %s, %s)",
                (product_id, product_name, category, price, stock, create_time)
            )
            product_ids.append(product_id)

    logger.info(f"生成 {len(product_ids)} 个商品")

    # 生成订单数据
    logger.info("生成订单数据...")
    for i in range(1500):
        order_id = i + 1
        user_id = random.choice(user_ids) if user_ids else 1
        product_id = random.choice(product_ids) if product_ids else 1
        quantity = random.randint(1, 10) if random.random() > 0.05 else random.randint(-5, 0)
        unit_price = generate_dirty_price() or round(random.uniform(10, 1000), 2)
        order_time = generate_dirty_date()
        status = random.choice(STATUSES)

        if order_time:
            cursor.execute(
                "INSERT INTO orders (order_id, user_id, product_id, quantity, unit_price, order_time, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (order_id, user_id, product_id, quantity, unit_price, order_time, status)
            )

    logger.info("生成 1500 条订单")

    # 生成日志数据
    logger.info("生成日志数据...")
    for i in range(2000):
        log_id = i + 1
        user_id = random.choice(user_ids) if user_ids else 1
        action = random.choice(ACTIONS)
        log_time = generate_dirty_date()
        description = f"User {user_id} performed {action}" if random.random() > 0.3 else None

        if log_time:
            cursor.execute(
                "INSERT INTO logs (log_id, user_id, action, log_time, description) VALUES (%s, %s, %s, %s, %s)",
                (log_id, user_id, action, log_time, description)
            )

    logger.info("生成 2000 条日志")
    logger.info("数据生成完成!")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("数据生成脚本")
    logger.info("=" * 50)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        generate_data(cursor)

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("数据已成功插入数据库!")

    except Error as e:
        logger.error(f"数据生成失败: {e}")


if __name__ == '__main__':
    main()
