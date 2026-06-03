"""
ETL系统主程序 - 电商销售数据多维分析系统
从source_db抽取数据，清洗转换后加载到dw_db星型模型数据仓库
"""

import mysql.connector
from mysql.connector import Error
import re
from datetime import datetime
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password'  # 请根据实际情况修改
}

# 源数据库和目标数据库名称
SOURCE_DB = 'source_db'
DW_DB = 'dw_db'


class ETLPipeline:
    """ETL流水线类"""

    def __init__(self):
        self.source_conn = None
        self.dw_conn = None
        self.stats = {
            'extracted': 0,
            'transformed': 0,
            'loaded': 0,
            'errors': 0
        }

    def connect_source(self):
        """连接源数据库"""
        try:
            self.source_conn = mysql.connector.connect(**DB_CONFIG)
            logger.info("源数据库连接成功")
            return True
        except Error as e:
            logger.error(f"源数据库连接失败: {e}")
            return False

    def connect_dw(self):
        """连接目标数据仓库"""
        try:
            self.dw_conn = mysql.connector.connect(**DB_CONFIG)
            logger.info("数据仓库连接成功")
            return True
        except Error as e:
            logger.error(f"数据仓库连接失败: {e}")
            return False

    def close_connections(self):
        """关闭数据库连接"""
        if self.source_conn and self.source_conn.is_connected():
            self.source_conn.close()
            logger.info("源数据库连接已关闭")
        if self.dw_conn and self.dw_conn.is_connected():
            self.dw_conn.close()
            logger.info("数据仓库连接已关闭")

    # ==================== 数据清洗方法 ====================

    @staticmethod
    def validate_phone(phone):
        """
        校验手机号是否有效
        中国手机号：1开头，11位数字
        """
        if phone is None:
            return False
        phone_str = str(phone).strip()
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone_str))

    @staticmethod
    def clean_price(price):
        """清洗价格：返回正数，无效返回None"""
        try:
            p = float(price)
            return p if p > 0 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_date(date_str):
        """
        统一日期格式为 YYYY-MM-DD HH:MM:SS
        支持多种输入格式
        """
        if date_str is None:
            return None

        date_str = str(date_str).strip()

        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y%m%d',
            '%Y%m%d%H%M%S'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue

        return None  # 无法解析

    @staticmethod
    def normalize_category(category):
        """
        标准化商品分类
        映射表：{'手机':'Electronics', '书籍':'Books', ...}
        """
        category_map = {
            '手机': 'Electronics',
            '电脑': 'Electronics',
            '平板': 'Electronics',
            '电视': 'Electronics',
            '相机': 'Electronics',
            '书籍': 'Books',
            '小说': 'Books',
            '技术': 'Books',
            '服装': 'Fashion',
            '鞋': 'Fashion',
            '包': 'Fashion',
            '食品': 'Food',
            '饮料': 'Food',
            '零食': 'Food',
            '家具': 'Home',
            '家电': 'Home',
            '玩具': 'Toys',
            '游戏': 'Toys'
        }

        return category_map.get(category, 'Others')

    @staticmethod
    def extract_date_dimensions(order_time):
        """
        从订单时间拆解出年/月/日
        """
        if order_time is None:
            return None, None, None, None

        try:
            if isinstance(order_time, str):
                dt = datetime.strptime(order_time, '%Y-%m-%d %H:%M:%S')
            else:
                dt = order_time

            return dt.year, dt.month, dt.day, dt
        except Exception:
            return None, None, None, None

    @staticmethod
    def calculate_total(quantity, unit_price):
        """计算总金额"""
        try:
            q = int(quantity)
            p = float(unit_price)
            return round(q * p, 2)
        except (ValueError, TypeError):
            return None

    # ==================== ETL 步骤 ====================

    def run_etl(self):
        """运行完整ETL流程"""
        logger.info("=" * 50)
        logger.info("ETL流程启动")
        logger.info("=" * 50)

        # 步骤1: 抽取
        if not self.extract():
            logger.error("抽取阶段失败，终止ETL")
            return False

        # 步骤2: 清洗转换
        if not self.transform():
            logger.error("转换阶段失败，终止ETL")
            return False

        # 步骤3: 加载
        if not self.load():
            logger.error("加载阶段失败，终止ETL")
            return False

        logger.info("=" * 50)
        logger.info("ETL流程完成!")
        logger.info(f"统计: 抽取={self.stats['extracted']}, "
                    f"转换={self.stats['transformed']}, "
                    f"加载={self.stats['loaded']}, "
                    f"错误={self.stats['errors']}")
        logger.info("=" * 50)

        return True

    def extract(self):
        """
        步骤1: 抽取（Extract）
        从source_db读取原始表数据
        """
        logger.info("[抽取阶段] 开始从源数据库读取数据...")

        try:
            cursor = self.source_conn.cursor(dictionary=True)

            # 抽取用户数据
            cursor.execute(f"SELECT * FROM {SOURCE_DB}.users")
            users = cursor.fetchall()
            logger.info(f"  - 用户表: 读取 {len(users)} 条记录")
            self.stats['extracted'] += len(users)

            # 抽取商品数据
            cursor.execute(f"SELECT * FROM {SOURCE_DB}.products")
            products = cursor.fetchall()
            logger.info(f"  - 商品表: 读取 {len(products)} 条记录")
            self.stats['extracted'] += len(products)

            # 抽取订单数据
            cursor.execute(f"SELECT * FROM {SOURCE_DB}.orders")
            orders = cursor.fetchall()
            logger.info(f"  - 订单表: 读取 {len(orders)} 条记录")
            self.stats['extracted'] += len(orders)

            # 抽取日志数据
            cursor.execute(f"SELECT * FROM {SOURCE_DB}.logs")
            logs = cursor.fetchall()
            logger.info(f"  - 日志表: 读取 {len(logs)} 条记录")
            self.stats['extracted'] += len(logs)

            cursor.close()

            # 将抽取的数据存储在实例变量中
            self.extracted_data = {
                'users': users,
                'products': products,
                'orders': orders,
                'logs': logs
            }

            logger.info("[抽取阶段] 完成!")
            return True

        except Error as e:
            logger.error(f"[抽取阶段] 错误: {e}")
            return False

    def transform(self):
        """
        步骤2: 清洗与转换（Transform）
        """
        logger.info("[转换阶段] 开始数据清洗与转换...")

        try:
            # 清洗转换用户数据
            clean_users = self._transform_users()
            logger.info(f"  - 用户清洗后: {len(clean_users)} 条有效记录")

            # 清洗转换商品数据
            clean_products = self._transform_products()
            logger.info(f"  - 商品清洗后: {len(clean_products)} 条有效记录")

            # 清洗转换订单数据
            clean_orders = self._transform_orders()
            logger.info(f"  - 订单清洗后: {len(clean_orders)} 条有效记录")

            # 清洗转换日志数据
            clean_logs = self._transform_logs()
            logger.info(f"  - 日志清洗后: {len(clean_logs)} 条有效记录")

            self.transformed_data = {
                'users': clean_users,
                'products': clean_products,
                'orders': clean_orders,
                'logs': clean_logs
            }

            self.stats['transformed'] = (
                len(clean_users) + len(clean_products) +
                len(clean_orders) + len(clean_logs)
            )

            logger.info("[转换阶段] 完成!")
            return True

        except Exception as e:
            logger.error(f"[转换阶段] 错误: {e}")
            return False

    def _transform_users(self):
        """清洗转换用户数据"""
        clean_users = []
        for user in self.extracted_data['users']:
            # 手机号校验
            if not self.validate_phone(user.get('phone')):
                self.stats['errors'] += 1
                continue

            clean_user = {
                'user_id': user.get('user_id'),
                'username': str(user.get('username', '')).strip(),
                'phone': str(user.get('phone', '')).strip(),
                'email': str(user.get('email', '')).strip() if user.get('email') else None,
                'register_time': self.normalize_date(user.get('register_time'))
            }

            if clean_user['register_time']:  # 只保留有效日期的记录
                clean_users.append(clean_user)

        return clean_users

    def _transform_products(self):
        """清洗转换商品数据"""
        clean_products = []
        for product in self.extracted_data['products']:
            # 价格必须大于0
            price = self.clean_price(product.get('price'))
            if price is None:
                self.stats['errors'] += 1
                continue

            # 日期标准化
            create_time = self.normalize_date(product.get('create_time'))

            clean_product = {
                'product_id': product.get('product_id'),
                'product_name': str(product.get('product_name', '')).strip(),
                'category': str(product.get('category', '')).strip(),
                'category_en': self.normalize_category(product.get('category')),
                'price': price,
                'stock': int(product.get('stock', 0)) if product.get('stock') else 0,
                'create_time': create_time
            }

            if clean_product['product_name'] and create_time:
                clean_products.append(clean_product)

        return clean_products

    def _transform_orders(self):
        """清洗转换订单数据"""
        clean_orders = []
        for order in self.extracted_data['orders']:
            # 日期标准化
            order_time = self.normalize_date(order.get('order_time'))
            if order_time is None:
                self.stats['errors'] += 1
                continue

            # 计算总金额
            total_amount = self.calculate_total(
                order.get('quantity'),
                order.get('unit_price')
            )

            if total_amount is None:
                self.stats['errors'] += 1
                continue

            # 提取日期维度
            year, month, day, dt = self.extract_date_dimensions(order_time)

            clean_order = {
                'order_id': order.get('order_id'),
                'user_id': order.get('user_id'),
                'product_id': order.get('product_id'),
                'quantity': int(order.get('quantity')),
                'unit_price': float(order.get('unit_price')),
                'total_amount': total_amount,
                'order_time': order_time,
                'year': year,
                'month': month,
                'day': day,
                'status': str(order.get('status', 'pending')).strip()
            }

            clean_orders.append(clean_order)

        return clean_orders

    def _transform_logs(self):
        """清洗转换日志数据"""
        clean_logs = []
        for log in self.extracted_data['logs']:
            # 日期标准化
            log_time = self.normalize_date(log.get('log_time'))
            if log_time is None:
                self.stats['errors'] += 1
                continue

            clean_log = {
                'log_id': log.get('log_id'),
                'user_id': log.get('user_id'),
                'action': str(log.get('action', '')).strip(),
                'log_time': log_time,
                'description': str(log.get('description', '')).strip() if log.get('description') else None
            }

            if clean_log['action']:
                clean_logs.append(clean_log)

        return clean_logs

    def load(self):
        """
        步骤3: 加载（Load）
        将清洗后数据插入dw_db的维度表和事实表
        处理重复数据（如用户已存在则更新，否则插入）
        """
        logger.info("[加载阶段] 开始加载数据到数据仓库...")

        try:
            # 加载用户维度
            self._load_dim_users()

            # 加载商品维度
            self._load_dim_products()

            # 加载日期维度
            self._load_dim_date()

            # 加载订单事实表
            self._load_fact_orders()

            # 加载日志事实表
            self._load_fact_logs()

            logger.info("[加载阶段] 完成!")
            return True

        except Exception as e:
            logger.error(f"[加载阶段] 错误: {e}")
            return False

    def _load_dim_users(self):
        """加载用户维度表 - 处理重复数据（更新或插入）"""
        logger.info("  - 加载用户维度表...")

        cursor = self.dw_conn.cursor()

        for user in self.transformed_data['users']:
            try:
                # 检查是否已存在
                cursor.execute(
                    f"SELECT user_key FROM {DW_DB}.dim_user WHERE user_id = %s",
                    (user['user_id'],)
                )
                result = cursor.fetchone()

                if result:
                    # 更新已存在记录
                    cursor.execute(
                        f"""UPDATE {DW_DB}.dim_user
                            SET username = %s, phone = %s, email = %s,
                                register_time = %s, update_time = NOW()
                            WHERE user_id = %s""",
                        (user['username'], user['phone'], user['email'],
                         user['register_time'], user['user_id'])
                    )
                else:
                    # 插入新记录
                    cursor.execute(
                        f"""INSERT INTO {DW_DB}.dim_user
                            (user_id, username, phone, email, register_time)
                            VALUES (%s, %s, %s, %s, %s)""",
                        (user['user_id'], user['username'], user['phone'],
                         user['email'], user['register_time'])
                    )
                    self.stats['loaded'] += 1

                self.dw_conn.commit()

            except Error as e:
                logger.error(f"  - 加载用户 {user['user_id']} 失败: {e}")
                self.dw_conn.rollback()

        cursor.close()
        logger.info(f"  - 用户维度表加载完成")

    def _load_dim_products(self):
        """加载商品维度表"""
        logger.info("  - 加载商品维度表...")

        cursor = self.dw_conn.cursor()

        for product in self.transformed_data['products']:
            try:
                cursor.execute(
                    f"SELECT product_key FROM {DW_DB}.dim_product WHERE product_id = %s",
                    (product['product_id'],)
                )
                result = cursor.fetchone()

                if result:
                    cursor.execute(
                        f"""UPDATE {DW_DB}.dim_product
                            SET product_name = %s, category = %s, category_en = %s,
                                price = %s, stock = %s, update_time = NOW()
                            WHERE product_id = %s""",
                        (product['product_name'], product['category'],
                         product['category_en'], product['price'],
                         product['stock'], product['product_id'])
                    )
                else:
                    cursor.execute(
                        f"""INSERT INTO {DW_DB}.dim_product
                            (product_id, product_name, category, category_en, price, stock)
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                        (product['product_id'], product['product_name'],
                         product['category'], product['category_en'],
                         product['price'], product['stock'])
                    )
                    self.stats['loaded'] += 1

                self.dw_conn.commit()

            except Error as e:
                logger.error(f"  - 加载商品 {product['product_id']} 失败: {e}")
                self.dw_conn.rollback()

        cursor.close()
        logger.info(f"  - 商品维度表加载完成")

    def _load_dim_date(self):
        """加载日期维度表"""
        logger.info("  - 加载日期维度表...")

        cursor = self.dw_conn.cursor()

        # 从订单数据中提取所有不同的日期
        dates = set()
        for order in self.transformed_data['orders']:
            if order['year']:
                dates.add((order['year'], order['month'], order['day']))

        for year, month, day in dates:
            try:
                # 构造完整日期
                date_str = f"{year}-{month:02d}-{day:02d} 00:00:00"

                # 检查是否已存在
                cursor.execute(
                    f"SELECT date_key FROM {DW_DB}.dim_date WHERE date_value = %s",
                    (date_str,)
                )
                result = cursor.fetchone()

                if not result:
                    # 计算季度和周
                    quarter = (month - 1) // 3 + 1
                    week_of_year = datetime(year, month, day).isocalendar()[1]

                    cursor.execute(
                        f"""INSERT INTO {DW_DB}.dim_date
                            (date_value, year, month, day, quarter, week_of_year)
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                        (date_str, year, month, day, quarter, week_of_year)
                    )
                    self.stats['loaded'] += 1
                    self.dw_conn.commit()

            except Error as e:
                logger.error(f"  - 加载日期 {year}-{month}-{day} 失败: {e}")
                self.dw_conn.rollback()

        cursor.close()
        logger.info(f"  - 日期维度表加载完成")

    def _load_fact_orders(self):
        """加载订单事实表"""
        logger.info("  - 加载订单事实表...")

        cursor = self.dw_conn.cursor()

        for order in self.transformed_data['orders']:
            try:
                # 获取用户维度键
                cursor.execute(
                    f"SELECT user_key FROM {DW_DB}.dim_user WHERE user_id = %s",
                    (order['user_id'],)
                )
                user_result = cursor.fetchone()
                if not user_result:
                    continue
                user_key = user_result[0]

                # 获取商品维度键
                cursor.execute(
                    f"SELECT product_key FROM {DW_DB}.dim_product WHERE product_id = %s",
                    (order['product_id'],)
                )
                product_result = cursor.fetchone()
                if not product_result:
                    continue
                product_key = product_result[0]

                # 获取日期维度键
                date_str = f"{order['year']}-{order['month']:02d}-{order['day']:02d} 00:00:00"
                cursor.execute(
                    f"SELECT date_key FROM {DW_DB}.dim_date WHERE date_value = %s",
                    (date_str,)
                )
                date_result = cursor.fetchone()
                if not date_result:
                    continue
                date_key = date_result[0]

                # 检查订单是否已存在（使用SCD Type 1更新）
                cursor.execute(
                    f"SELECT order_key FROM {DW_DB}.fact_orders WHERE order_id = %s",
                    (order['order_id'],)
                )
                result = cursor.fetchone()

                if result:
                    # 更新
                    cursor.execute(
                        f"""UPDATE {DW_DB}.fact_orders
                            SET user_key = %s, product_key = %s, date_key = %s,
                                quantity = %s, unit_price = %s, total_amount = %s,
                                status = %s, update_time = NOW()
                            WHERE order_id = %s""",
                        (user_key, product_key, date_key,
                         order['quantity'], order['unit_price'],
                         order['total_amount'], order['status'],
                         order['order_id'])
                    )
                else:
                    # 插入
                    cursor.execute(
                        f"""INSERT INTO {DW_DB}.fact_orders
                            (order_id, user_key, product_key, date_key,
                             quantity, unit_price, total_amount, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (order['order_id'], user_key, product_key, date_key,
                         order['quantity'], order['unit_price'],
                         order['total_amount'], order['status'])
                    )
                    self.stats['loaded'] += 1

                self.dw_conn.commit()

            except Error as e:
                logger.error(f"  - 加载订单 {order['order_id']} 失败: {e}")
                self.dw_conn.rollback()

        cursor.close()
        logger.info(f"  - 订单事实表加载完成")

    def _load_fact_logs(self):
        """加载日志事实表"""
        logger.info("  - 加载日志事实表...")

        cursor = self.dw_conn.cursor()

        for log in self.transformed_data['logs']:
            try:
                # 检查日志是否已存在
                cursor.execute(
                    f"SELECT log_key FROM {DW_DB}.fact_logs WHERE log_id = %s",
                    (log['log_id'],)
                )
                result = cursor.fetchone()

                if not result:
                    cursor.execute(
                        f"""INSERT INTO {DW_DB}.fact_logs
                            (log_id, user_id, action, log_time, description)
                            VALUES (%s, %s, %s, %s, %s)""",
                        (log['log_id'], log['user_id'], log['action'],
                         log['log_time'], log['description'])
                    )
                    self.stats['loaded'] += 1
                    self.dw_conn.commit()

            except Error as e:
                logger.error(f"  - 加载日志 {log['log_id']} 失败: {e}")
                self.dw_conn.rollback()

        cursor.close()
        logger.info(f"  - 日志事实表加载完成")


def main():
    """主函数"""
    print("=" * 60)
    print("电商销售数据 ETL 系统")
    print("=" * 60)

    # 创建ETL管道
    etl = ETLPipeline()

    # 连接数据库
    if not etl.connect_source():
        print("错误: 无法连接源数据库!")
        return

    if not etl.connect_dw():
        print("错误: 无法连接数据仓库!")
        etl.close_connections()
        return

    # 运行ETL
    success = etl.run_etl()

    # 关闭连接
    etl.close_connections()

    if success:
        print("\nETL执行成功!")
    else:
        print("\nETL执行失败!")


if __name__ == '__main__':
    main()
