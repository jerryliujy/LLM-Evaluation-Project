"""
数据库重构后的数据导入和测试脚本
支持新的数据结构：
- 专家回答与原始回答多对多关系
- 标准问题与标准回答一对一关系
- 标准回答对原始回答和专家回答的引用
"""

import json
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# 添加backend路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.database import SessionLocal, engine
from app import models, schemas
from app.crud import crud_expert_answer, crud_std_question, crud_std_answer

def create_tables():
    """创建所有表"""
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")

def import_expert_answers(db: Session):
    """导入专家回答数据"""
    print("\nImporting expert answers...")
    
    try:
        with open('test_data/expert_answers_data_new.json', 'r', encoding='utf-8') as f:
            expert_answers_data = json.load(f)
        
        count = 0
        for answer_data in expert_answers_data:
            try:
                # 转换日期格式
                if 'created_at' in answer_data:
                    # 移除created_at，让数据库使用默认值
                    del answer_data['created_at']
                
                expert_answer = schemas.ExpertAnswerCreate(**answer_data)
                crud_expert_answer.create_expert_answer(db, expert_answer)
                count += 1
                print(f"  ✓ Created expert answer {count}: Question {answer_data['question_id']}")
                
            except Exception as e:
                print(f"  ✗ Error creating expert answer for question {answer_data.get('question_id', 'unknown')}: {e}")
        
        print(f"✓ Successfully imported {count} expert answers")
        
    except FileNotFoundError:
        print("✗ Expert answers data file not found")
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing expert answers JSON: {e}")
    except Exception as e:
        print(f"✗ Unexpected error importing expert answers: {e}")

def import_standard_qa(db: Session):
    """导入标准问答数据"""
    print("\nImporting standard Q&A data...")
    
    try:
        with open('test_data/standard_qa_data_new.json', 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        count = 0
        for qa in qa_data:
            try:
                # 处理嵌套的std_answer数据
                if 'std_answer' in qa and qa['std_answer']:
                    # 确保std_answer有正确的字段
                    std_answer_data = qa['std_answer']
                    if 'created_by' not in std_answer_data:
                        std_answer_data['created_by'] = qa.get('created_by')
                
                std_question = schemas.StdQuestionCreate(**qa)
                created_question = crud_std_question.create_std_question(db, std_question)
                count += 1
                print(f"  ✓ Created standard Q&A {count}: {qa['text'][:50]}...")
                
            except Exception as e:
                print(f"  ✗ Error creating standard Q&A {count + 1}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"✓ Successfully imported {count} standard Q&A pairs")
        
    except FileNotFoundError:
        print("✗ Standard Q&A data file not found")
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing standard Q&A JSON: {e}")
    except Exception as e:
        print(f"✗ Unexpected error importing standard Q&A: {e}")

def test_crud_operations(db: Session):
    """测试CRUD操作"""
    print("\nTesting CRUD operations...")
    
    try:
        # 测试专家回答查询
        print("  Testing expert answer queries...")
        expert_answers = crud_expert_answer.get_expert_answers_paginated(db, limit=3)
        print(f"    ✓ Found {expert_answers['total']} expert answers")
        
        if expert_answers['data']:
            first_answer = expert_answers['data'][0]
            print(f"    ✓ First answer references {len(first_answer.referenced_raw_answers)} raw answers")
        
        # 测试标准问题查询
        print("  Testing standard question queries...")
        std_questions = crud_std_question.get_std_questions_paginated(db, limit=3)
        print(f"    ✓ Found {std_questions.total} standard questions")
        
        if std_questions.data:
            first_question = std_questions.data[0]
            if hasattr(first_question, 'std_answer') and first_question.std_answer:
                print(f"    ✓ First question has standard answer: {first_question.std_answer.answer[:50]}...")
                if first_question.std_answer.raw_answer_id:
                    print(f"    ✓ Standard answer references raw answer ID: {first_question.std_answer.raw_answer_id}")
                if first_question.std_answer.expert_answer_id:
                    print(f"    ✓ Standard answer references expert answer ID: {first_question.std_answer.expert_answer_id}")
        
        print("  ✓ CRUD operations test completed successfully")
        
    except Exception as e:
        print(f"  ✗ Error during CRUD testing: {e}")
        import traceback
        traceback.print_exc()

def verify_relationships(db: Session):
    """验证数据关系"""
    print("\nVerifying data relationships...")
    
    try:
        # 验证专家回答与原始回答的多对多关系
        expert_answer = db.query(models.ExpertAnswer).first()
        if expert_answer:
            ref_count = len(expert_answer.referenced_raw_answers)
            print(f"  ✓ Expert answer {expert_answer.id} references {ref_count} raw answers")
        
        # 验证标准问题与标准回答的一对一关系
        std_question = db.query(models.StdQuestion).first()
        if std_question and hasattr(std_question, 'std_answer'):
            if std_question.std_answer:
                print(f"  ✓ Standard question {std_question.id} has one standard answer")
            else:
                print(f"  ! Standard question {std_question.id} has no standard answer")
        
        # 验证标准回答的引用关系
        std_answer = db.query(models.StdAnswer).first()
        if std_answer:
            refs = []
            if std_answer.raw_answer_id:
                refs.append(f"raw answer {std_answer.raw_answer_id}")
            if std_answer.expert_answer_id:
                refs.append(f"expert answer {std_answer.expert_answer_id}")
            if refs:
                print(f"  ✓ Standard answer {std_answer.id} references: {', '.join(refs)}")
            else:
                print(f"  ! Standard answer {std_answer.id} has no references")
        
        print("  ✓ Relationship verification completed")
        
    except Exception as e:
        print(f"  ✗ Error during relationship verification: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=== Database Restructure Import & Test Script ===")
    print(f"Started at: {datetime.now()}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 1. 创建表
        create_tables()
        
        # 2. 导入专家回答
        import_expert_answers(db)
        
        # 3. 导入标准问答
        import_standard_qa(db)
        
        # 4. 测试CRUD操作
        test_crud_operations(db)
        
        # 5. 验证关系
        verify_relationships(db)
        
        print(f"\n=== Import & Test Completed Successfully ===")
        print(f"Finished at: {datetime.now()}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
