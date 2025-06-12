"""
LLM客户端服务 - 支持OpenAI兼容的API调用
包括阿里云通义千问、OpenAI、以及其他兼容的API提供商
"""
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from openai import AsyncOpenAI
from decimal import Decimal
import json

from ..config.llm_config import get_default_evaluation_prompt, calculate_cost

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端，支持多种API提供商"""
    
    def __init__(self, api_key: str, base_url: str = None, model_name: str = "qwen-plus", cost_per_1k_tokens: float = 0.0006):
        """
        初始化LLM客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL，默认为阿里云通义千问
            model_name: 模型名称
            cost_per_1k_tokens: 每1k tokens的成本
        """
        self.model_name = model_name
        self.api_key = api_key
        self.cost_per_1k_tokens = cost_per_1k_tokens
        
        # 默认使用阿里云通义千问的API端点
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    async def generate_answer(
        self, 
        question: str, 
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_k: int = 50,
        enable_reasoning: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成问题的回答
        
        Args:
            question: 问题内容
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            top_k: Top-K采样
            enable_reasoning: 启用推理模式
            **kwargs: 其他参数
            
        Returns:
            包含回答内容和元数据的字典
        """
        try:
            messages = []
            
            # 添加系统提示词
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加用户问题
            messages.append({"role": "user", "content": question})
            
            # 准备API参数
            api_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            # 添加top_k参数（如果支持）
            if top_k and top_k != 50:  # 只在非默认值时添加
                api_params["top_k"] = top_k
            
            # 添加推理模式参数（如果支持）
            if enable_reasoning:
                api_params["enable_reasoning"] = True
            
            # 调用API
            completion = await self.client.chat.completions.create(**api_params)
            
            # 提取回答内容
            answer_content = completion.choices[0].message.content            # 计算使用量和成本
            usage_info = {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0
            }
            # 使用实例的成本参数
            cost = calculate_cost(usage_info, self.cost_per_1k_tokens)
            
            # 返回结果
            return {
                "success": True,
                "answer": answer_content,
                "usage": usage_info,
                "cost": cost,
                "model": completion.model,
                "finish_reason": completion.choices[0].finish_reason,
                "prompt_used": system_prompt,
                "raw_response": completion.model_dump() if hasattr(completion, 'model_dump') else str(completion)
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": None
            }
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        evaluation_prompt: str = None,
        correct_answer: str = None,
        question_type: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """
        评测答案质量
        
        Args:
            question: 原问题
            answer: 待评测的答案
            evaluation_prompt: 评测提示词
            correct_answer: 标准答案（用于参考）
            question_type: 问题类型 (choice/text)
            **kwargs: 其他参数
            
        Returns:
            包含评分和评测详情的字典
        """
        try:
            # 构建评测提示词
            if not evaluation_prompt:
                evaluation_prompt = get_default_evaluation_prompt(question_type)
            
            # 格式化评测提示词
            evaluation_content = evaluation_prompt.format(
                question=question,
                answer=answer,
                correct_answer=correct_answer or ""
            )
            
            messages = [
                {"role": "system", "content": "你是一个专业的问答评测专家，请客观公正地评测答案质量。"},
                {"role": "user", "content": evaluation_content}
            ]
            
            # 调用API进行评测
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # 评测时使用较低的temperature保证一致性
                max_tokens=1000,
                **kwargs
            )
            
            evaluation_text = completion.choices[0].message.content
            
            # 尝试解析JSON格式的评测结果
            try:
                evaluation_result = json.loads(evaluation_text)
                score = float(evaluation_result.get("score", 0))
                reasoning = evaluation_result.get("reasoning", "")
                feedback = evaluation_result.get("feedback", "")
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON格式，尝试从文本中提取分数
                score = self._extract_score_from_text(evaluation_text)
                reasoning = evaluation_text
                feedback = evaluation_text            # 计算成本
            usage_info = {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0
            }
            cost = calculate_cost(usage_info, self.cost_per_1k_tokens)
            
            return {
                "success": True,
                "score": min(100, max(0, score)),  # 确保分数在0-100范围内
                "reasoning": reasoning,
                "feedback": feedback,
                "evaluation_prompt": evaluation_content,
                "raw_evaluation": evaluation_text,
                "usage": usage_info,
                "cost": cost
            }
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "score": 0
            }
    
    def _extract_score_from_text(self, text: str) -> float:
        """从文本中提取分数"""
        import re
        
        # 尝试匹配常见的分数格式
        patterns = [
            r'(\d+(?:\.\d+)?)\s*分',
            r'评分[：:]\s*(\d+(?:\.\d+)?)',
            r'分数[：:]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*/\s*100',
            r'(\d+(?:\.\d+)?)%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    score = float(match.group(1))
                    # 如果是百分比格式，直接返回
                    if '%' in match.group(0):
                        return score
                    # 如果分数大于100，假设是百分制
                    if score > 100:
                        return min(100, score)
                    return score
                except ValueError:
                    continue
        
        # 如果没有找到明确的分数，返回默认值
        return 60.0
    
    async def close(self):
        """关闭客户端连接"""
        if hasattr(self.client, 'close'):
            await self.client.close()





# 全局客户端缓存
_client_cache: Dict[str, LLMClient] = {}


async def get_llm_client(
    api_key: str, 
    db_llm = None
) -> LLMClient:
    """
    获取或创建LLM客户端（带缓存）
    
    Args:
        api_key: API密钥
        db_llm: 数据库中的LLM模型实例（必须提供）
        
    Returns:
        LLM客户端实例
    """
    if not db_llm:
        raise ValueError("db_llm is required for creating LLM client")
    
    # 创建缓存键
    cache_key = f"{db_llm.id}:{api_key}"
    
    if cache_key not in _client_cache:
        # 直接使用数据库模型创建客户端
        _client_cache[cache_key] = LLMClient(
            api_key=api_key,
            base_url=db_llm.api_endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name=db_llm.name,
            cost_per_1k_tokens=float(db_llm.cost_per_1k_tokens) if db_llm.cost_per_1k_tokens else 0.0006
        )
    
    return _client_cache[cache_key]


async def cleanup_clients():
    """清理所有客户端连接"""
    for client in _client_cache.values():
        await client.close()
    _client_cache.clear()
