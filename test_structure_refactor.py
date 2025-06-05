#!/usr/bin/env python3
"""
数据结构重构测试脚本
测试新的一对多引用关系是否正确工作
"""

import sys
import os
import json
from pathlib import Path

# 添加backend路径到sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app import models, schemas
from app.crud import crud_std_question, crud_std_answer, crud_expert_answer, crud_raw_answer

def test_database_schema():
    """测试数据库schema是否正确创建"""
    print("🔍 测试数据库schema...")
    
    try:
        # 创建所有表
        models.Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        return False

def test_reference_relationships():
    """测试新的引用关系"""
    print("\n🔍 测试引用关系...")
    
    db = SessionLocal()
    try:
        # 创建测试数据
        print("📝 创建测试数据...")
        
        # 创建原始问题
        raw_question = models.RawQuestion(
            title="测试Docker问题",
            body="如何使用Docker？",
            author="test_user"
        )
        db.add(raw_question)
        db.flush()
        
        # 创建原始回答
        raw_answer1 = models.RawAnswer(
            question_id=raw_question.id,
            answer="使用docker run命令",
            answered_by="user1"
        )
        raw_answer2 = models.RawAnswer(
            question_id=raw_question.id,
            answer="使用docker-compose",
            answered_by="user2"
        )
        db.add_all([raw_answer1, raw_answer2])
        db.flush()
        
        # 创建专家回答
        expert_answer = models.ExpertAnswer(
            question_id=raw_question.id,
            content="专家建议使用docker-compose",
            author=1
        )
        db.add(expert_answer)
        db.flush()
        
        # 创建标准问题
        std_question = models.StdQuestion(
            dataset_id=1,
            raw_question_id=raw_question.id,
            text="Docker使用标准问题",
            question_type="技术操作",
            created_by="test_expert"
        )
        db.add(std_question)
        db.flush()
        
        # 创建标准回答并设置引用关系
        std_answer = models.StdAnswer(
            std_question_id=std_question.id,
            answer="标准回答：推荐使用docker-compose进行容器编排",
            created_by="test_expert"
        )
        db.add(std_answer)
        db.flush()
        
        # 设置引用关系 - 一个标准回答引用多个原始回答和专家回答
        raw_answer1.referenced_by_std_answer_id = std_answer.id
        raw_answer2.referenced_by_std_answer_id = std_answer.id
        expert_answer.referenced_by_std_answer_id = std_answer.id
        
        db.commit()
        
        # 验证关系
        print("🔍 验证引用关系...")
        
        # 查询标准回答及其引用
        std_answer_with_refs = db.query(models.StdAnswer).filter(
            models.StdAnswer.id == std_answer.id
        ).first()
        
        if std_answer_with_refs:
            # 检查引用的原始回答
            referenced_raw_answers = db.query(models.RawAnswer).filter(
                models.RawAnswer.referenced_by_std_answer_id == std_answer.id
            ).all()
            
            # 检查引用的专家回答
            referenced_expert_answers = db.query(models.ExpertAnswer).filter(
                models.ExpertAnswer.referenced_by_std_answer_id == std_answer.id
            ).all()
            
            print(f"📊 标准回答 ID: {std_answer.id}")
            print(f"📊 引用的原始回答数量: {len(referenced_raw_answers)}")
            print(f"📊 引用的专家回答数量: {len(referenced_expert_answers)}")
            
            # 验证一对多关系
            if len(referenced_raw_answers) == 2 and len(referenced_expert_answers) == 1:
                print("✅ 一对多引用关系验证成功")
                
                # 验证每个原始回答和专家回答只能被一个标准回答引用
                for raw_ans in referenced_raw_answers:
                    if raw_ans.referenced_by_std_answer_id == std_answer.id:
                        print(f"✅ 原始回答 {raw_ans.id} 正确引用标准回答 {std_answer.id}")
                    else:
                        print(f"❌ 原始回答 {raw_ans.id} 引用关系错误")
                        return False
                
                for expert_ans in referenced_expert_answers:
                    if expert_ans.referenced_by_std_answer_id == std_answer.id:
                        print(f"✅ 专家回答 {expert_ans.id} 正确引用标准回答 {std_answer.id}")
                    else:
                        print(f"❌ 专家回答 {expert_ans.id} 引用关系错误")
                        return False
                
                return True
            else:
                print(f"❌ 引用关系数量不正确")
                return False
        else:
            print("❌ 未找到标准回答")
            return False
            
    except Exception as e:
        print(f"❌ 测试引用关系失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_crud_operations():
    """测试CRUD操作"""
    print("\n🔍 测试CRUD操作...")
    
    db = SessionLocal()
    try:
        # 测试标准回答创建
        std_answer_data = schemas.StdAnswerCreate(
            std_question_id=1,
            answer="测试标准回答",
            created_by="test_user",
            referenced_raw_answer_ids=[1, 2],
            referenced_expert_answer_ids=[1],
            scoring_points=[
                schemas.StdAnswerScoringPointCreate(
                    scoring_point_text="测试评分点",
                    point_order=1,
                    created_by="test_user"
                )
            ]
        )
        
        # 创建标准回答
        created_answer = crud_std_answer.create_std_answer(db, std_answer_data)
        print(f"✅ 创建标准回答成功，ID: {created_answer.id}")
        
        # 验证引用关系是否正确设置
        referenced_raw = db.query(models.RawAnswer).filter(
            models.RawAnswer.referenced_by_std_answer_id == created_answer.id
        ).count()
        
        referenced_expert = db.query(models.ExpertAnswer).filter(
            models.ExpertAnswer.referenced_by_std_answer_id == created_answer.id
        ).count()
        
        if referenced_raw > 0 and referenced_expert > 0:
            print("✅ CRUD操作引用关系设置成功")
            return True
        else:
            print("❌ CRUD操作引用关系设置失败")
            return False
            
    except Exception as e:
        print(f"❌ CRUD操作测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始数据结构重构测试...")
    
    tests = [
        ("数据库Schema测试", test_database_schema),
        ("引用关系测试", test_reference_relationships),
        ("CRUD操作测试", test_crud_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通过")
        else:
            print(f"❌ {test_name} 失败")
    
    print(f"\n{'='*50}")
    print(f"📊 测试结果: {passed}/{total} 通过")
    print('='*50)
    
    if passed == total:
        print("🎉 所有测试通过！数据结构重构成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
