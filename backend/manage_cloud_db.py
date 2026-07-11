"""
云端数据库管理脚本
使用方法：
1. 修改下面的数据库连接信息
2. 运行 python manage_cloud_db.py
"""

import pymysql
from pymysql.cursors import DictCursor

# 云端数据库连接配置
DB_CONFIG = {
    'host': '你的云端数据库地址',  # 例如: rm-xxx.mysql.rds.aliyuncs.com
    'port': 3306,
    'user': '你的数据库用户名',
    'password': '你的数据库密码',
    'database': 'quanmailian',
    'charset': 'utf8mb4'
}


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG, cursorclass=DictCursor)


def execute_query(sql, params=None):
    """执行查询语句"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute_update(sql, params=None):
    """执行更新语句"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()


def list_tables():
    """列出所有表"""
    sql = "SHOW TABLES"
    results = execute_query(sql)
    print("数据库中的表:")
    for row in results:
        print(f"  - {list(row.values())[0]}")


def get_table_info(table_name):
    """获取表结构"""
    sql = f"DESCRIBE {table_name}"
    results = execute_query(sql)
    print(f"\n表 {table_name} 的结构:")
    for row in results:
        print(f"  {row['Field']}: {row['Type']} {'NOT NULL' if row['Null'] == 'NO' else 'NULL'}")


def count_records(table_name):
    """统计表记录数"""
    sql = f"SELECT COUNT(*) as count FROM {table_name}"
    result = execute_query(sql)[0]
    print(f"\n表 {table_name} 有 {result['count']} 条记录")


def query_users(limit=10):
    """查询用户列表"""
    sql = f"SELECT user_id, nickname, phone, email, created_at FROM user LIMIT {limit}"
    results = execute_query(sql)
    print(f"\n用户列表（前{limit}条）:")
    for row in results:
        print(f"  ID: {row['user_id']}, 昵称: {row['nickname']}, 手机: {row['phone']}")


def main():
    """主函数"""
    print("=" * 50)
    print("云端数据库管理工具")
    print("=" * 50)

    try:
        # 测试连接
        conn = get_connection()
        conn.close()
        print("✓ 数据库连接成功!\n")

        # 显示基本信息
        list_tables()

        # 如果需要查看特定表的信息，取消下面的注释
        # get_table_info('user')
        # count_records('user')
        # query_users(5)

    except Exception as e:
        print(f"✗ 连接失败: {e}")
        print("\n请检查:")
        print("1. 数据库连接信息是否正确")
        print("2. 服务器防火墙是否允许你的IP访问")
        print("3. 数据库用户是否有远程访问权限")


if __name__ == '__main__':
    main()
