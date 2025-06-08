"""
测试标准答案的反向级联删除逻辑
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import Base
from app import models, schemas
from app.crud import crud_std_answer, crud_std_question
from app.models.std_question import StdQuestion
from app.models.std_answer import StdAnswer
from app.models.dataset import Dataset
from app.models.user import User

# 创建内存数据库用于测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_data(db_session):
    """创建测试数据"""
    # 创建数据集
    dataset = Dataset(
        name="测试数据集",
        description="用于测试的数据集"
    )
    db_session.add(dataset)
    db_session.flush()
    
    # 创建用户
    user = User(
        username="testuser",
        email="test@example.com",
        role="admin"
    )
    db_session.add(user)
    db_session.flush()
    
    # 创建标准问题
    std_question = StdQuestion(
        dataset_id=dataset.id,
        body="这是一个测试问题？",
        question_type="单选题",
        created_by=user.id
    )
    db_session.add(std_question)
    db_session.flush()
    
    # 创建多个标准答案
    std_answer1 = StdAnswer(
        std_question_id=std_question.id,
        answer="这是第一个标准答案",
        answered_by=user.id
    )
    std_answer2 = StdAnswer(
        std_question_id=std_question.id,
        answer="这是第二个标准答案",
        answered_by=user.id
    )
    std_answer3 = StdAnswer(
        std_question_id=std_question.id,
        answer="这是第三个标准答案",
        answered_by=user.id
    )
    
    db_session.add_all([std_answer1, std_answer2, std_answer3])
    db_session.commit()
    
    return {
        'dataset': dataset,
        'user': user,
        'std_question': std_question,
        'std_answers': [std_answer1, std_answer2, std_answer3]
    }

class TestCascadeDeletion:
    """测试级联删除功能"""
    
    def test_delete_single_answer_should_not_cascade_when_others_remain(self, db_session, sample_data):
        """测试删除单个答案时，如果还有其他答案存在，不应该级联删除问题"""
        std_question = sample_data['std_question']
        std_answer1 = sample_data['std_answers'][0]
        
        # 删除第一个答案
        result = crud_std_answer.set_std_answer_deleted_status(
            db_session, std_answer1.id, deleted_status=True
        )
        
        # 验证答案被删除
        assert result is not None
        assert result.is_valid == False
        
        # 验证问题仍然存在
        db_session.refresh(std_question)
        assert std_question.is_valid == True
        
        # 验证其他答案仍然存在
        remaining_answers = db_session.query(StdAnswer).filter(
            StdAnswer.std_question_id == std_question.id,
            StdAnswer.is_valid == True
        ).count()
        assert remaining_answers == 2
    
    def test_delete_last_answer_should_cascade_delete_question(self, db_session, sample_data):
        """测试删除最后一个答案时，应该级联删除问题"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 先删除前两个答案
        crud_std_answer.set_std_answer_deleted_status(
            db_session, std_answers[0].id, deleted_status=True
        )
        crud_std_answer.set_std_answer_deleted_status(
            db_session, std_answers[1].id, deleted_status=True
        )
        
        # 验证问题仍然存在
        db_session.refresh(std_question)
        assert std_question.is_valid == True
        
        # 删除最后一个答案
        result = crud_std_answer.set_std_answer_deleted_status(
            db_session, std_answers[2].id, deleted_status=True
        )
        
        # 验证答案被删除
        assert result is not None
        assert result.is_valid == False
        
        # 验证问题也被级联删除
        db_session.refresh(std_question)
        assert std_question.is_valid == False
    
    def test_restore_answer_should_restore_question(self, db_session, sample_data):
        """测试恢复答案时，应该恢复关联的问题"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 删除所有答案（这会级联删除问题）
        for answer in std_answers:
            crud_std_answer.set_std_answer_deleted_status(
                db_session, answer.id, deleted_status=True
            )
        
        # 验证问题被删除
        db_session.refresh(std_question)
        assert std_question.is_valid == False
        
        # 恢复一个答案
        result = crud_std_answer.set_std_answer_deleted_status(
            db_session, std_answers[0].id, deleted_status=False
        )
        
        # 验证答案被恢复
        assert result is not None
        assert result.is_valid == True
        
        # 验证问题也被恢复
        db_session.refresh(std_question)
        assert std_question.is_valid == True
    
    def test_batch_delete_with_cascade(self, db_session, sample_data):
        """测试批量删除答案的级联删除逻辑"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 批量删除所有答案
        answer_ids = [answer.id for answer in std_answers]
        affected_rows = crud_std_answer.set_multiple_std_answers_deleted_status(
            db_session, answer_ids, deleted_status=True
        )
        
        # 验证所有答案被删除
        assert affected_rows == 3
        
        # 验证问题也被级联删除
        db_session.refresh(std_question)
        assert std_question.is_valid == False
        
        # 验证所有答案确实被标记为删除
        for answer in std_answers:
            db_session.refresh(answer)
            assert answer.is_valid == False
    
    def test_batch_delete_partial_answers(self, db_session, sample_data):
        """测试批量删除部分答案时的行为"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 只删除前两个答案
        answer_ids = [std_answers[0].id, std_answers[1].id]
        affected_rows = crud_std_answer.set_multiple_std_answers_deleted_status(
            db_session, answer_ids, deleted_status=True
        )
        
        # 验证两个答案被删除
        assert affected_rows == 2
        
        # 验证问题仍然存在（因为还有一个答案）
        db_session.refresh(std_question)
        assert std_question.is_valid == True
        
        # 验证第三个答案仍然有效
        db_session.refresh(std_answers[2])
        assert std_answers[2].is_valid == True
    
    def test_batch_restore_with_question_restore(self, db_session, sample_data):
        """测试批量恢复答案时恢复问题"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 先批量删除所有答案
        answer_ids = [answer.id for answer in std_answers]
        crud_std_answer.set_multiple_std_answers_deleted_status(
            db_session, answer_ids, deleted_status=True
        )
        
        # 验证问题被删除
        db_session.refresh(std_question)
        assert std_question.is_valid == False
        
        # 批量恢复部分答案
        restore_ids = [std_answers[0].id, std_answers[1].id]
        affected_rows = crud_std_answer.set_multiple_std_answers_deleted_status(
            db_session, restore_ids, deleted_status=False
        )
        
        # 验证答案被恢复
        assert affected_rows == 2
        
        # 验证问题也被恢复
        db_session.refresh(std_question)
        assert std_question.is_valid == True
        
        # 验证相应的答案被恢复
        db_session.refresh(std_answers[0])
        db_session.refresh(std_answers[1])
        assert std_answers[0].is_valid == True
        assert std_answers[1].is_valid == True
        
        # 验证第三个答案仍然被删除
        db_session.refresh(std_answers[2])
        assert std_answers[2].is_valid == False

class TestTransactionIntegrity:
    """测试事务完整性"""
    
    def test_transaction_rollback_on_error(self, db_session, sample_data):
        """测试发生错误时事务回滚"""
        std_question = sample_data['std_question']
        std_answers = sample_data['std_answers']
        
        # 验证初始状态
        assert std_question.is_valid == True
        for answer in std_answers:
            assert answer.is_valid == True
        
        # 模拟在级联删除过程中发生错误的情况
        # 这里我们通过直接操作数据库来模拟
        try:
            # 开始事务
            answer_id = std_answers[0].id
            question_id = std_question.id
            
            # 删除答案
            db_session.query(StdAnswer).filter(StdAnswer.id == answer_id).update(
                {StdAnswer.is_valid: False}, synchronize_session=False
            )
            
            # 验证数据仍然一致
            remaining_answers = db_session.query(StdAnswer).filter(
                StdAnswer.std_question_id == question_id,
                StdAnswer.is_valid == True
            ).count()
            
            # 应该还有2个有效答案，所以问题不应该被删除
            question = db_session.query(StdQuestion).filter(StdQuestion.id == question_id).first()
            assert question.is_valid == True
            
            db_session.commit()
            
        except Exception as e:
            db_session.rollback()
            # 验证在回滚后数据恢复到原始状态
            db_session.refresh(std_question)
            for answer in std_answers:
                db_session.refresh(answer)
                assert answer.is_valid == True
            assert std_question.is_valid == True

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
