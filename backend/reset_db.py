#!/usr/bin/env python3
"""
重置数据库脚本 - 删除所有表并重新创建
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL
from app.models import Base

def reset_database():
    """重置数据库"""
    try:
        # 创建引擎
        engine = create_engine(DATABASE_URL)
        
        print("正在连接数据库...")
        
        # 删除所有表
        print("正在删除所有现有表...")
        with engine.connect() as conn:
            # 禁用外键检查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            # 获取所有表名
            result = conn.execute(text("SHOW TABLES;"))
            tables = [row[0] for row in result]
            
            # 删除所有表
            for table in tables:
                print(f"删除表: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`;"))
            
            # 重新启用外键检查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()
        
        # 重新创建所有表
        print("正在创建新的表结构...")
        Base.metadata.create_all(bind=engine)
        
        print("数据库重置完成！")
        
    except Exception as e:
        print(f"重置数据库时出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    reset_database()
