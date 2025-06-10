#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加版本管理系统相关字段和表
创建日期：2025年6月10日
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456@localhost:3306/llm")

def migrate_database():
    """执行数据库迁移"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # 开始事务
        trans = connection.begin()
        
        try:
            print("开始数据库迁移...")
            
            # 1. 为 StdQuestion 表添加新字段
            print("1. 为 StdQuestion 表添加新字段...")
            try:
                connection.execute(text("""
                    ALTER TABLE `StdQuestion` 
                    ADD COLUMN `original_dataset_id` INT DEFAULT NULL COMMENT '原始数据集ID（用于跨数据集引用）',
                    ADD COLUMN `current_dataset_id` INT DEFAULT NULL COMMENT '当前数据集ID（用于跨数据集引用）'
                """))
                print("   - StdQuestion 表字段添加成功")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("   - StdQuestion 表字段已存在，跳过")
                else:
                    raise e
            
            # 2. 为 StdAnswer 表添加新字段
            print("2. 为 StdAnswer 表添加新字段...")
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswer` 
                    ADD COLUMN `original_dataset_id` INT DEFAULT NULL COMMENT '原始数据集ID（用于跨数据集引用）',
                    ADD COLUMN `current_dataset_id` INT DEFAULT NULL COMMENT '当前数据集ID（用于跨数据集引用）'
                """))
                print("   - StdAnswer 表字段添加成功")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("   - StdAnswer 表字段已存在，跳过")
                else:
                    raise e
            
            # 3. 为 StdAnswerScoringPoint 表添加新字段
            print("3. 为 StdAnswerScoringPoint 表添加新字段...")
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswerScoringPoint` 
                    ADD COLUMN `original_dataset_id` INT DEFAULT NULL COMMENT '原始数据集ID（用于跨数据集引用）',
                    ADD COLUMN `current_dataset_id` INT DEFAULT NULL COMMENT '当前数据集ID（用于跨数据集引用）'
                """))
                print("   - StdAnswerScoringPoint 表字段添加成功")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("   - StdAnswerScoringPoint 表字段已存在，跳过")
                else:
                    raise e
            
            # 4. 创建 DatasetVersion 表
            print("4. 创建 DatasetVersion 表...")
            try:
                connection.execute(text("""
                    CREATE TABLE `DatasetVersion` (
                      `id` INT NOT NULL AUTO_INCREMENT,
                      `dataset_id` INT NOT NULL,
                      `name` VARCHAR(255) NOT NULL,
                      `description` TEXT DEFAULT NULL,
                      `version_number` VARCHAR(50) NOT NULL,
                      `is_committed` TINYINT(1) NOT NULL DEFAULT 0,
                      `is_public` TINYINT(1) NOT NULL DEFAULT 0,
                      `created_by` INT NOT NULL,
                      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      `committed_at` DATETIME DEFAULT NULL,
                      PRIMARY KEY (`id`),
                      INDEX `idx_version_dataset` (`dataset_id`),
                      INDEX `idx_version_created_by` (`created_by`),
                      INDEX `idx_version_committed` (`is_committed`),
                      INDEX `idx_version_public` (`is_public`),
                      UNIQUE INDEX `idx_version_dataset_number` (`dataset_id`, `version_number`),
                      CONSTRAINT `fk_version_dataset`
                        FOREIGN KEY (`dataset_id`) REFERENCES `Dataset` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_version_user`
                        FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """))
                print("   - DatasetVersion 表创建成功")
            except Exception as e:
                if "already exists" in str(e):
                    print("   - DatasetVersion 表已存在，跳过")
                else:
                    raise e
            
            # 5. 创建 VersionStdQuestion 表
            print("5. 创建 VersionStdQuestion 表...")
            try:
                connection.execute(text("""
                    CREATE TABLE `VersionStdQuestion` (
                      `id` INT NOT NULL AUTO_INCREMENT,
                      `version_id` INT NOT NULL,
                      `original_question_id` INT DEFAULT NULL,
                      `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
                      `is_new` TINYINT(1) NOT NULL DEFAULT 0,
                      `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
                      `modified_body` TEXT DEFAULT NULL,
                      `modified_question_type` ENUM('choice', 'text') DEFAULT NULL,
                      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (`id`),
                      INDEX `idx_vq_version` (`version_id`),
                      INDEX `idx_vq_original` (`original_question_id`),
                      INDEX `idx_vq_modified` (`is_modified`),
                      INDEX `idx_vq_new` (`is_new`),
                      INDEX `idx_vq_deleted` (`is_deleted`),
                      CONSTRAINT `fk_vq_version`
                        FOREIGN KEY (`version_id`) REFERENCES `DatasetVersion` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_vq_original`
                        FOREIGN KEY (`original_question_id`) REFERENCES `StdQuestion` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """))
                print("   - VersionStdQuestion 表创建成功")
            except Exception as e:
                if "already exists" in str(e):
                    print("   - VersionStdQuestion 表已存在，跳过")
                else:
                    raise e
            
            # 6. 创建 VersionStdAnswer 表
            print("6. 创建 VersionStdAnswer 表...")
            try:
                connection.execute(text("""
                    CREATE TABLE `VersionStdAnswer` (
                      `id` INT NOT NULL AUTO_INCREMENT,
                      `version_id` INT NOT NULL,
                      `version_question_id` INT NOT NULL,
                      `original_answer_id` INT DEFAULT NULL,
                      `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
                      `is_new` TINYINT(1) NOT NULL DEFAULT 1,
                      `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
                      `modified_answer` TEXT DEFAULT NULL,
                      `modified_answered_by` INT DEFAULT NULL,
                      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (`id`),
                      INDEX `idx_va_version` (`version_id`),
                      INDEX `idx_va_vquestion` (`version_question_id`),
                      INDEX `idx_va_original` (`original_answer_id`),
                      INDEX `idx_va_modified` (`is_modified`),
                      INDEX `idx_va_new` (`is_new`),
                      INDEX `idx_va_deleted` (`is_deleted`),
                      CONSTRAINT `fk_va_version`
                        FOREIGN KEY (`version_id`) REFERENCES `DatasetVersion` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_va_vquestion`
                        FOREIGN KEY (`version_question_id`) REFERENCES `VersionStdQuestion` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_va_original`
                        FOREIGN KEY (`original_answer_id`) REFERENCES `StdAnswer` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_va_answered_by`
                        FOREIGN KEY (`modified_answered_by`) REFERENCES `User` (`id`)
                        ON DELETE SET NULL ON UPDATE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """))
                print("   - VersionStdAnswer 表创建成功")
            except Exception as e:
                if "already exists" in str(e):
                    print("   - VersionStdAnswer 表已存在，跳过")
                else:
                    raise e
            
            # 7. 创建 VersionScoringPoint 表
            print("7. 创建 VersionScoringPoint 表...")
            try:
                connection.execute(text("""
                    CREATE TABLE `VersionScoringPoint` (
                      `id` INT NOT NULL AUTO_INCREMENT,
                      `version_id` INT NOT NULL,
                      `version_answer_id` INT NOT NULL,
                      `original_point_id` INT DEFAULT NULL,
                      `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
                      `is_new` TINYINT(1) NOT NULL DEFAULT 1,
                      `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
                      `modified_answer` TEXT DEFAULT NULL,
                      `modified_point_order` INT DEFAULT NULL,
                      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (`id`),
                      INDEX `idx_vsp_version` (`version_id`),
                      INDEX `idx_vsp_vanswer` (`version_answer_id`),
                      INDEX `idx_vsp_original` (`original_point_id`),
                      INDEX `idx_vsp_modified` (`is_modified`),
                      INDEX `idx_vsp_new` (`is_new`),
                      INDEX `idx_vsp_deleted` (`is_deleted`),
                      CONSTRAINT `fk_vsp_version`
                        FOREIGN KEY (`version_id`) REFERENCES `DatasetVersion` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_vsp_vanswer`
                        FOREIGN KEY (`version_answer_id`) REFERENCES `VersionStdAnswer` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                      CONSTRAINT `fk_vsp_original`
                        FOREIGN KEY (`original_point_id`) REFERENCES `StdAnswerScoringPoint` (`id`)
                        ON DELETE CASCADE ON UPDATE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """))
                print("   - VersionScoringPoint 表创建成功")
            except Exception as e:
                if "already exists" in str(e):
                    print("   - VersionScoringPoint 表已存在，跳过")
                else:
                    raise e
            
            # 8. 添加外键约束（如果不存在）
            print("8. 添加外键约束...")
            
            # StdQuestion 外键约束
            try:
                connection.execute(text("""
                    ALTER TABLE `StdQuestion`
                    ADD CONSTRAINT `fk_stdquestion_original_dataset`
                      FOREIGN KEY (`original_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE,
                    ADD CONSTRAINT `fk_stdquestion_current_dataset`
                      FOREIGN KEY (`current_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE
                """))
                print("   - StdQuestion 外键约束添加成功")
            except Exception as e:
                if "Duplicate foreign key constraint name" in str(e) or "already exists" in str(e):
                    print("   - StdQuestion 外键约束已存在，跳过")
                else:
                    raise e
            
            # StdAnswer 外键约束
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswer`
                    ADD CONSTRAINT `fk_stdanswer_original_dataset`
                      FOREIGN KEY (`original_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE,
                    ADD CONSTRAINT `fk_stdanswer_current_dataset`
                      FOREIGN KEY (`current_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE
                """))
                print("   - StdAnswer 外键约束添加成功")
            except Exception as e:
                if "Duplicate foreign key constraint name" in str(e) or "already exists" in str(e):
                    print("   - StdAnswer 外键约束已存在，跳过")
                else:
                    raise e
            
            # StdAnswerScoringPoint 外键约束
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswerScoringPoint`
                    ADD CONSTRAINT `fk_sasp_original_dataset`
                      FOREIGN KEY (`original_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE,
                    ADD CONSTRAINT `fk_sasp_current_dataset`
                      FOREIGN KEY (`current_dataset_id`) REFERENCES `Dataset` (`id`)
                      ON DELETE SET NULL ON UPDATE CASCADE
                """))
                print("   - StdAnswerScoringPoint 外键约束添加成功")
            except Exception as e:
                if "Duplicate foreign key constraint name" in str(e) or "already exists" in str(e):
                    print("   - StdAnswerScoringPoint 外键约束已存在，跳过")
                else:
                    raise e
            
            # 9. 添加索引（如果不存在）
            print("9. 添加索引...")
            
            try:
                connection.execute(text("""
                    ALTER TABLE `StdQuestion`
                    ADD INDEX `idx_stdquestion_original_dataset` (`original_dataset_id`),
                    ADD INDEX `idx_stdquestion_current_dataset` (`current_dataset_id`)
                """))
                print("   - StdQuestion 索引添加成功")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("   - StdQuestion 索引已存在，跳过")
                else:
                    raise e
            
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswer`
                    ADD INDEX `idx_stdanswer_original_dataset` (`original_dataset_id`),
                    ADD INDEX `idx_stdanswer_current_dataset` (`current_dataset_id`)
                """))
                print("   - StdAnswer 索引添加成功")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("   - StdAnswer 索引已存在，跳过")
                else:
                    raise e
            
            try:
                connection.execute(text("""
                    ALTER TABLE `StdAnswerScoringPoint`
                    ADD INDEX `idx_sasp_original_dataset` (`original_dataset_id`),
                    ADD INDEX `idx_sasp_current_dataset` (`current_dataset_id`)
                """))
                print("   - StdAnswerScoringPoint 索引添加成功")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("   - StdAnswerScoringPoint 索引已存在，跳过")
                else:
                    raise e
            
            # 提交事务
            trans.commit()
            print("\n✅ 数据库迁移完成！")
            print("版本管理系统已成功部署到数据库。")
            
        except Exception as e:
            # 回滚事务
            trans.rollback()
            print(f"\n❌ 迁移失败: {e}")
            raise e

if __name__ == "__main__":
    migrate_database()
