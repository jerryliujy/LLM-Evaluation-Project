"""
LLM配置文件
包含默认提示词和评估提示词配置，模型信息存储在数据库中
"""
import os
from typing import Optional, Dict, Any

# 默认系统提示词配置
DEFAULT_SYSTEM_PROMPTS = {
    "choice": """你是一个专业的问答助手。请仔细阅读问题和选项，选择最合适的答案。
请按照以下格式回答：
答案：[选项字母]
解释：[简要说明选择理由]""",
    
    "text": """你是一个专业的问答助手。请根据问题提供准确、详细、有用的回答。
回答要求：
1. 内容准确，逻辑清晰
2. 语言简洁明了
3. 针对问题的核心要点进行回答"""
}

# 默认评估提示词配置
DEFAULT_EVALUATION_PROMPTS = {
    "choice": """请评估以下选择题的回答质量：

评估标准：
1. 答案正确性 (50分)：是否选择了正确的选项
2. 解释合理性 (30分)：解释是否逻辑清晰、合理
3. 格式规范性 (20分)：是否按照要求的格式回答

问题：{question}
标准答案：{correct_answer}
待评估回答：{answer}

重要提示：请严格按照以下JSON格式返回评分结果，不要添加任何其他文字或格式标记：
{{
    "score": 85,
    "reasoning": "答案正确，解释清晰合理，格式规范",
    "feedback": "回答质量很好，但可以在解释部分提供更多细节"
}}""",
    
    "text": """请根据以下标准评估文本回答质量：

评估标准：
1. 准确性 (40分)：内容是否正确、符合事实
2. 完整性 (30分)：是否全面回答了问题的各个方面
3. 清晰性 (20分)：表达是否清楚、逻辑是否清晰
4. 实用性 (10分)：回答是否对提问者有帮助

问题：{question}
{f"参考答案：{correct_answer}" if correct_answer else ""}
待评估回答：{answer}

重要提示：请严格按照以下JSON格式返回评分结果，不要添加任何其他文字或格式标记：
{{
    "score": 85,
    "reasoning": "内容准确，覆盖全面，表达清晰",
    "feedback": "很好的回答，建议可以提供更多实例说明"
}}"""
}


def get_default_system_prompt(question_type: str = "text") -> str:
    """获取默认系统提示词"""
    return DEFAULT_SYSTEM_PROMPTS.get(question_type, DEFAULT_SYSTEM_PROMPTS["text"])


def get_default_evaluation_prompt(question_type: str = "text") -> str:
    """获取默认评估提示词"""
    return DEFAULT_EVALUATION_PROMPTS.get(question_type, DEFAULT_EVALUATION_PROMPTS["text"])


def get_api_key_from_env(model_name: str) -> Optional[str]:
    """从环境变量获取API密钥"""
    # 根据模型名称推断API密钥环境变量名
    if "qwen" in model_name.lower():
        return os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    elif "gpt" in model_name.lower() or "openai" in model_name.lower():
        return os.getenv("OPENAI_API_KEY")
    elif "chatglm" in model_name.lower():
        return os.getenv("CHATGLM_API_KEY")
    else:
        # 通用API密钥
        return os.getenv("LLM_API_KEY")


def calculate_cost(usage: Dict[str, Any], cost_per_1k_tokens: float) -> float:
    """计算API调用成本"""
    total_tokens = usage.get("total_tokens", 0)
    return (total_tokens / 1000) * cost_per_1k_tokens
