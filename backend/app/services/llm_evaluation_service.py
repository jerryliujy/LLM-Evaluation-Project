"""
Background task service for LLM evaluation
"""
import asyncio
import json
import time
import hashlib
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import logging

from ..db.database import get_db
from ..models.llm_evaluation_task import LLMEvaluationTask, TaskStatus
from ..models.std_question import StdQuestion
from ..models.llm import LLM
from ..models.llm_answer import LLMAnswer
from ..models.evaluation import Evaluation, EvaluatorType
from ..crud.crud_llm_evaluation_task import update_llm_evaluation_task, get_llm_evaluation_task
from ..schemas.llm_evaluation_task import LLMEvaluationTaskUpdate
from .llm_client_service import get_llm_client, LLMClient
from ..config.llm_config import get_api_key_from_env

logger = logging.getLogger(__name__)


class LLMEvaluationTaskProcessor:
    """LLM评测任务处理器"""
    
    def __init__(self):
        self.running_tasks: Dict[int, asyncio.Task] = {}
        
    async def process_evaluation_task_async(self, task_id: int, question_limit: Optional[int] = None):
        """异步处理评测任务"""
        from ..db.database import SessionLocal
        db = SessionLocal()        
        try:
            logger.info(f"=== 开始处理评测任务 {task_id} ===")
            
            # 获取任务
            logger.info(f"Task {task_id}: 步骤1 - 获取任务信息")
            task = get_llm_evaluation_task(db, task_id)
            if not task:
                logger.error(f"Task {task_id}: 任务不存在")
                return
            logger.info(f"Task {task_id}: 任务获取成功，状态: {task.status}")
              
            # 更新任务状态为运行中
            logger.info(f"Task {task_id}: 步骤2 - 更新任务状态为RUNNING")
            try:
                update_data = LLMEvaluationTaskUpdate(
                    status=TaskStatus.RUNNING,
                    started_at=datetime.now()
                )
                logger.info(f"Task {task_id}: 创建更新数据对象成功")
                
                result = update_llm_evaluation_task(db, task_id, update_data)
                logger.info(f"Task {task_id}: 更新任务状态完成，结果: {result is not None}")
                
            except Exception as update_error:
                logger.error(f"Task {task_id}: 更新任务状态时发生错误: {str(update_error)}")
                import traceback
                logger.error(f"Task {task_id}: 更新状态错误堆栈:\n{traceback.format_exc()}")
                raise            logger.info(f"Task {task_id}: 更新任务状态为RUNNING成功")
            
            # 获取数据集问题
            logger.info(f"Task {task_id}: 步骤3 - 获取数据集问题")
            try:
                questions = db.query(StdQuestion).filter(
                    StdQuestion.current_dataset_id == task.dataset_id,
                    StdQuestion.is_valid == True
                ).order_by(StdQuestion.id).all()
                
                logger.info(f"Task {task_id}: 找到 {len(questions)} 个问题，数据集ID: {task.dataset_id}")
                
                if question_limit:
                    questions = questions[:question_limit]
                    logger.info(f"Task {task_id}: 限制为 {len(questions)} 个问题")
                
                if not questions:
                    logger.error(f"Task {task_id}: 数据集 {task.dataset_id} 中没有找到问题")
                    return
                    
            except Exception as query_error:
                logger.error(f"Task {task_id}: 查询数据集问题时发生错误: {str(query_error)}")
                import traceback
                logger.error(f"Task {task_id}: 查询问题错误堆栈:\n{traceback.format_exc()}")
                raise
            
            # 更新总问题数
            update_data = LLMEvaluationTaskUpdate(total_questions=len(questions))
            update_llm_evaluation_task(db, task_id, update_data)
            # 获取或创建LLM记录
            llm = self._get_or_create_llm(db, task.model.name if task.model else task.model_name, 
                                          task.model.version if task.model else "default")
            logger.info(f"Using LLM: {llm.name} (ID: {llm.id})")      # 获取LLM客户端
            api_key = self._decrypt_api_key(task.api_key_hash)
            logger.info(f"API key found: {bool(api_key)}")
            if api_key:
                logger.info(f"API key length: {len(api_key)}")
                logger.info(f"API key prefix: {api_key[:10]}..." if len(api_key) > 10 else f"API key: {api_key}")
            
            if not api_key:
                logger.error("No API key available for task")
                update_data = LLMEvaluationTaskUpdate(
                    status=TaskStatus.FAILED,
                    error_message="No API key available"
                )
                update_llm_evaluation_task(db, task_id, update_data)
                return
            
            try:
                llm_client = await get_llm_client(
                    api_key=api_key,
                    db_llm=task.model  # 传递数据库模型信息
                )
                logger.info(f"Created LLM client for model: {llm_client.model_name}")
            except Exception as client_error:
                logger.error(f"Failed to create LLM client: {str(client_error)}")
                update_data = LLMEvaluationTaskUpdate(
                    status=TaskStatus.FAILED,
                    error_message=f"Failed to create LLM client: {str(client_error)}"
                )
                update_llm_evaluation_task(db, task_id, update_data)
                return
            
            completed_count = 0
            failed_count = 0
            
            for i, question in enumerate(questions):
                try:
                    logger.info(f"Processing question {i+1}/{len(questions)}: {question.id}")
                    # 检查任务是否被取消
                    current_task = get_llm_evaluation_task(db, task_id)
                    if current_task.status == TaskStatus.CANCELLED.value:
                        logger.info(f"Task {task_id} was cancelled")
                        break
                    
                    # 更新当前进度
                    progress = int((i / len(questions)) * 100)
                    update_data = LLMEvaluationTaskUpdate(
                        progress=progress,
                        completed_questions=i
                    )
                    update_llm_evaluation_task(db, task_id, update_data)                    
                    # 生成答案
                    start_time = time.time()
                    logger.info(f"Generating answer for question: {question.body[:100]}...")
                    
                    # 根据问题类型选择合适的system prompt
                    question_type = getattr(question, 'type', 'text')  # 默认为text类型
                    if question_type == 'choice':
                        from ..config.llm_config import get_default_system_prompt
                        system_prompt = get_default_system_prompt('choice')
                    else:
                        from ..config.llm_config import get_default_system_prompt  
                        system_prompt = get_default_system_prompt('text')
                    
                    # 如果任务有自定义system prompt，使用它
                    if task.system_prompt:
                        system_prompt = task.system_prompt
                    
                    answer_result = await llm_client.generate_answer(
                        question=question.body,
                        system_prompt=system_prompt,
                        temperature=float(task.temperature) if task.temperature else 0.7,
                        max_tokens=task.max_tokens or 2000,
                        top_k=task.top_k or 50,
                        enable_reasoning=task.enable_reasoning or False
                    )
                    response_time = int((time.time() - start_time) * 1000)  # 毫秒
                    logger.info(f"Got answer result - success: {answer_result['success']}")
                    if answer_result["success"]:
                        logger.info(f"Task {task_id}: 第{i+1}题 - 获得成功答案: {answer_result['answer'][:100]}...")
                        
                        # 创建LLM答案记录
                        logger.info(f"Task {task_id}: 第{i+1}题 - 开始创建LLMAnswer对象")
                        try:
                            llm_answer = LLMAnswer(
                                llm_id=llm.id,
                                task_id=task_id,  # 使用task_id作为evaluation_task_id
                                std_question_id=question.id,
                                prompt_used=self._build_prompt(system_prompt, question.body),
                                answer=answer_result["answer"],
                                is_valid=True
                            )
                            logger.info(f"Task {task_id}: 第{i+1}题 - LLMAnswer对象创建成功")
                            
                            logger.info(f"Task {task_id}: 第{i+1}题 - 开始添加到数据库")
                            db.add(llm_answer)
                            logger.info(f"Task {task_id}: 第{i+1}题 - 已添加到session，开始commit")
                            
                            db.commit()
                            logger.info(f"Task {task_id}: 第{i+1}题 - commit成功，开始refresh")
                            
                            db.refresh(llm_answer)
                            logger.info(f"Task {task_id}: 第{i+1}题 - LLM答案保存成功，ID: {llm_answer.id}")
                            
                        except Exception as save_error:
                            logger.error(f"Task {task_id}: 第{i+1}题 - 保存LLM答案时发生错误: {str(save_error)}")
                            import traceback
                            logger.error(f"Task {task_id}: 第{i+1}题 - 保存答案错误堆栈:\n{traceback.format_exc()}")
                            # 回滚事务
                            db.rollback()
                            raise
                        
                        completed_count += 1
                        
                        # 如果配置了自动评估
                        if task.evaluation_llm_id:
                            await self._perform_auto_evaluation(
                                db, question, llm_answer, 
                                task.evaluation_llm_id, task.evaluation_prompt,
                                api_key
                            )
                    else:
                        # 记录失败
                        llm_answer = LLMAnswer(
                            llm_id=llm.id,
                            task_id=task_id,
                            std_question_id=question.id,
                            prompt_used=self._build_prompt(task.system_prompt, question.body),
                            answer=f"API调用失败: {answer_result.get('error', 'Unknown error')}",
                            is_valid=False
                        )
                        db.add(llm_answer)
                        db.commit()
                        
                        failed_count += 1
                        logger.error(f"Failed to get answer for question {question.id}: {answer_result.get('error')}")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing question {question.id}: {str(e)}")
                
                # 小延迟避免API限流
                await asyncio.sleep(0.1)
              # 生成结果摘要
            result_summary = self._generate_result_summary(db, task_id)
            
            # 更新任务完成状态
            update_data = LLMEvaluationTaskUpdate(
                status=TaskStatus.COMPLETED,
                progress=100,
                completed_questions=completed_count,
                failed_questions=failed_count,
                completed_at=datetime.now(),
                result_summary=result_summary
            )
            update_llm_evaluation_task(db, task_id, update_data)
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            # 更新任务失败状态
            update_data = LLMEvaluationTaskUpdate(
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
            update_llm_evaluation_task(db, task_id, update_data)
        finally:
            db.close()
            logger.info(f"Task {task_id} completed")
    
    def _get_or_create_llm(self, db: Session, model_name: str, model_version: Optional[str] = None) -> LLM:
        """获取或创建LLM记录"""
        try:
            logger.info(f"_get_or_create_llm: 开始查找LLM，model_name={model_name}, model_version={model_version}")
            
            # 修复查询条件 - 分别处理有版本号和默认版本的情况
            version_to_search = model_version or text("default")
            llm = db.query(LLM).filter(
                LLM.name == model_name,
                LLM.version == version_to_search
            ).first()
            
            logger.info(f"_get_or_create_llm: 查询结果: {llm is not None}")
            
            if not llm:
                logger.info(f"_get_or_create_llm: LLM不存在，准备创建新的LLM记录")
                
                llm = LLM(
                    name=model_name,
                    display_name=model_name,  # 添加必需的字段
                    provider="API",           # 添加必需的字段
                    version=model_version or "default",
                    affiliation="API"
                )
                logger.info(f"_get_or_create_llm: LLM对象创建成功，准备添加到数据库")
                
                db.add(llm)
                logger.info(f"_get_or_create_llm: 已添加到session，准备commit")
                
                db.commit()
                logger.info(f"_get_or_create_llm: commit成功，准备refresh")
                
                db.refresh(llm)
                logger.info(f"_get_or_create_llm: refresh成功，LLM创建完成，ID: {llm.id}")
            else:
                logger.info(f"_get_or_create_llm: 找到现有LLM，ID: {llm.id}")
            
            return llm
            
        except Exception as e:
            logger.error(f"_get_or_create_llm: 出错: {str(e)}")
            import traceback
            logger.error(f"_get_or_create_llm: 错误堆栈:\n{traceback.format_exc()}")
            raise
    
    def _build_prompt(self, system_prompt: Optional[str], question_body: str) -> str:
        """构建完整的提示词"""
        if system_prompt:
            return f"{system_prompt}\n\n用户问题: {question_body}"
        return question_body    
    
    def _decrypt_api_key(self, api_key_hash: Optional[str]) -> Optional[str]:
        """解密API密钥 (临时实现：直接返回存储的密钥)，实际应该要进行加密"""
        if not api_key_hash:
            # 尝试从环境变量获取默认密钥
            default_key = get_api_key_from_env('QWEN_API_KEY')
            if default_key:
                logger.info("Using default API key from environment")
                return default_key
            return None
        # 临时实现：直接返回存储的API密钥（不安全，仅用于测试）
        # TODO: 实现真实的解密逻辑
        return api_key_hash
    
    async def _perform_auto_evaluation(
        self, 
        db: Session,
        question: StdQuestion, 
        llm_answer: LLMAnswer,
        evaluation_llm_id: int,
        evaluation_prompt: Optional[str],
        api_key: str
    ):
        """执行自动评估"""
        try:
            # 获取标准答案
            std_answers = question.std_answers
            if not std_answers:
                return
            
            # 获取评估LLM
            evaluation_llm = db.query(LLM).filter(LLM.id == evaluation_llm_id).first()
            if not evaluation_llm:
                return
              # 获取LLM客户端进行评估
            llm_client = await get_llm_client(
                api_key=api_key,
                db_llm=evaluation_llm
            )
            
            # 调用异步评估LLM
            evaluation_result = await self._call_evaluation_llm(
                llm_client,
                question.body,
                llm_answer.answer,
                std_answers[0].answer if std_answers else "",
                evaluation_prompt,
                question.type if hasattr(question, 'type') else "text"
            )
            
            if evaluation_result["success"]:
                # 创建评估记录
                evaluation = Evaluation(
                    std_question_id=question.id,
                    llm_answer_id=llm_answer.id,
                    score=evaluation_result["score"],
                    evaluator_type=EvaluatorType.AUTO,
                    evaluator_id=evaluation_llm_id,
                    reasoning=evaluation_result["reasoning"],
                    evaluation_prompt=evaluation_result["evaluation_prompt"]
                )
                db.add(evaluation)
                db.commit()
            
        except Exception as e:
            logger.error(f"Auto evaluation failed: {str(e)}")
    
    async def _call_evaluation_llm(
        self,
        llm_client: LLMClient,
        question: str,
        answer: str,
        correct_answer: str = "",
        evaluation_prompt: Optional[str] = None,
        question_type: str = "text"
    ) -> Dict[str, Any]:
        """使用LLM客户端调用评估LLM"""
        try:
            # 使用LLM客户端的评估功能
            result = await llm_client.evaluate_answer(
                question=question,
                answer=answer,
                evaluation_prompt=evaluation_prompt,
                correct_answer=correct_answer,
                question_type=question_type
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation LLM call failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "score": 0,
                "reasoning": f"评估失败: {str(e)}"
            }
    
    def _generate_result_summary(self, db: Session, task_id: int) -> Dict[str, Any]:
        """生成任务结果摘要"""
        try:
            # 获取任务相关的所有答案
            answers = db.query(LLMAnswer).filter(LLMAnswer.task_id == task_id).all()
            
            total_answers = len(answers)
            valid_answers = len([a for a in answers if a.is_valid])
            failed_answers = total_answers - valid_answers
            
            # 计算成本和token使用 - 由于字段已移除，设为默认值
            total_cost = Decimal("0")  # API字段已移除
            total_tokens = 0  # API字段已移除
            avg_response_time = 0  # API字段已移除
            
            # 获取评估分数
            evaluations = db.query(Evaluation).join(LLMAnswer).filter(LLMAnswer.task_id == task_id).all()
            scores = [e.score for e in evaluations if e.score is not None]
            avg_score = sum(scores) / len(scores) if scores else None
            
            return {
                "total_questions": total_answers,
                "valid_answers": valid_answers,
                "failed_answers": failed_answers,
                "success_rate": valid_answers / total_answers if total_answers > 0 else 0,
                "total_cost": float(total_cost),
                "total_tokens": total_tokens,
                "average_response_time": avg_response_time,
                "evaluations_count": len(evaluations),
                "average_score": float(avg_score) if avg_score else None
            }
        except Exception as e:
            logger.error(f"Failed to generate result summary: {str(e)}")
            return {"error": str(e)}
    
    def get_task_status(self, task_id: int) -> str:
        """获取任务运行状态"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if task.done():
                del self.running_tasks[task_id]
                return "completed"
            return "running"
        return "not_running"
    
    async def start_task_async(self, task_id: int):
        """异步启动任务"""
        if task_id in self.running_tasks:
            return False  # 任务已在运行
        
        # 创建异步任务
        task = asyncio.create_task(self.process_evaluation_task_async(task_id))
        self.running_tasks[task_id] = task
        return True    
    
    def process_evaluation_task(self, task_id: int, question_limit: Optional[int] = None):
        """同步处理评测任务（用于FastAPI BackgroundTasks）"""
        try:
            # 在新的事件循环中运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.process_evaluation_task_async(task_id, question_limit))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in sync task processing: {str(e)}")            # 更新任务状态为失败
            try:
                from ..db.database import SessionLocal
                db = SessionLocal()                
                try:
                    update_data = LLMEvaluationTaskUpdate(
                        status=TaskStatus.FAILED,
                        error_message=str(e),
                        completed_at=datetime.now()
                    )
                    update_llm_evaluation_task(db, task_id, update_data)
                finally:
                    db.close()
            except Exception as update_error:
                logger.error(f"Failed to update task status: {str(update_error)}")


# 全局任务处理器实例
task_processor = LLMEvaluationTaskProcessor()
