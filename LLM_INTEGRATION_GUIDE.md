# LLM评估系统 - OpenAI兼容API集成说明

## 📖 概述

本系统已成功集成了OpenAI兼容的API调用功能，支持多种大语言模型，包括阿里云通义千问、OpenAI GPT系列、智谱ChatGLM等。采用工厂模式设计，易于扩展和维护。

## 🏗️ 架构设计

### 核心组件

1. **LLMClient**: 统一的LLM客户端，支持问答生成和自动评估
2. **LLMClientFactory**: 工厂类，根据模型类型创建相应的客户端
3. **LLMEvaluationTaskProcessor**: 评估任务处理器，支持异步批量处理
4. **配置管理**: 统一的模型配置和提示词管理

### 文件结构

```
backend/
├── app/
│   ├── config/
│   │   └── llm_config.py          # 模型配置和提示词
│   ├── services/
│   │   ├── llm_client_service.py  # LLM客户端服务
│   │   └── llm_evaluation_service.py # 评估任务服务
│   └── routers/
│       └── llm_evaluation.py      # API路由
├── test_qwen_api.py               # Qwen API测试脚本
├── test_integration.py            # 完整集成测试
└── .env.example                   # 环境变量示例
```

## 🔧 支持的模型

| 模型系列 | 模型名称 | 提供商 | API端点 |
|---------|---------|---------|---------|
| **通义千问** | qwen-plus, qwen-turbo, qwen-max | Alibaba Cloud | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| **GPT系列** | gpt-3.5-turbo, gpt-4, gpt-4-turbo | OpenAI | https://api.openai.com/v1 |
| **ChatGLM** | chatglm | ZhipuAI | https://open.bigmodel.cn/api/paas/v4 |

## ⚙️ 配置步骤

### 1. 环境变量配置

复制 `.env.example` 为 `.env` 并填入API密钥：

```env
# 阿里云通义千问
QWEN_API_KEY=your_qwen_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# 智谱ChatGLM
CHATGLM_API_KEY=your_chatglm_api_key_here
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python test_integration.py
```

## 🚀 使用方法

### 基本用法

```python
from app.services.llm_client_service import get_llm_client

# 获取LLM客户端
client = await get_llm_client(
    model_name="qwen-plus",
    api_key="your-api-key"
)

# 生成回答
result = await client.generate_answer(
    question="什么是人工智能？",
    system_prompt="你是一个AI专家。",
    temperature=0.7,
    max_tokens=2000
)

# 评估答案
evaluation = await client.evaluate_answer(
    question="什么是人工智能？",
    answer="AI是模拟人类智能的技术",
    question_type="text"
)

await client.close()
```

### 工厂模式使用

```python
from app.services.llm_client_service import LLMClientFactory

# 使用工厂创建客户端
client = LLMClientFactory.create_client(
    model_name="gpt-4",
    api_key="your-openai-key",
    api_endpoint="https://api.openai.com/v1"
)
```

### 评估任务处理

```python
from app.services.llm_evaluation_service import task_processor

# 启动异步评估任务
success = await task_processor.start_task_async(task_id=123)

# 检查任务状态
status = task_processor.get_task_status(task_id=123)
```

## 🎯 核心功能

### 1. 问答生成 (`generate_answer`)

- 支持自定义系统提示词
- 可调节温度参数和最大token数
- 自动计算使用量和成本
- 错误处理和重试机制

### 2. 自动评估 (`evaluate_answer`)

- 支持选择题和开放题评估
- 智能提取评分和反馈
- JSON格式化输出
- 评估提示词可自定义

### 3. 批量处理

- 异步任务队列
- 实时进度跟踪
- 失败重试机制
- 结果汇总统计

## 📊 前端集成

### API端点

- `GET /llm-evaluation/models` - 获取支持的模型列表
- `POST /llm-evaluation/tasks` - 创建评估任务
- `GET /llm-evaluation/tasks/{task_id}` - 获取任务状态

### 前端工作流

1. **数据集选择** - 选择要评估的问题数据集
2. **模型配置** - 选择模型、设置API密钥和参数
3. **系统提示词** - 配置问答和评估提示词
4. **答案生成** - 批量生成LLM回答
5. **自动评估** - 使用评估LLM打分
6. **结果查看** - 查看评估结果和统计

## 🔒 安全考虑

### API密钥管理

- 前端密钥加密传输
- 后端密钥加密存储
- 任务完成后自动清理
- 支持环境变量注入

### 错误处理

- API调用失败重试
- 异常信息记录
- 用户友好错误提示
- 系统稳定性保障

## 🧪 测试脚本

### 1. API功能测试

```bash
python test_qwen_api.py
```

### 2. 集成测试

```bash
python test_integration.py
```

### 3. 单元测试

```bash
# 测试LLM客户端
python -m pytest tests/test_llm_client.py

# 测试评估服务
python -m pytest tests/test_evaluation_service.py
```

## 🔧 自定义配置

### 添加新模型

在 `app/config/llm_config.py` 中添加模型配置：

```python
LLM_CONFIGS["your-model"] = {
    "api_endpoint": "https://your-api.com/v1",
    "default_temperature": 0.7,
    "default_max_tokens": 2000,
    "cost_per_1k_tokens": 0.001,
    "description": "您的模型描述"
}
```

### 自定义评估提示词

```python
DEFAULT_EVALUATION_PROMPTS["custom_type"] = """
您的自定义评估提示词模板
问题：{question}
回答：{answer}
标准答案：{correct_answer}
"""
```

## 📈 性能优化

### 1. 连接池管理

- 客户端缓存机制
- 连接复用
- 自动清理过期连接

### 2. 并发控制

- 异步请求处理
- 限流保护
- 错误恢复

### 3. 成本控制

- Token使用统计
- 成本实时计算
- 预算警告机制

## 🚨 故障排除

### 常见问题

1. **API密钥错误**
   - 检查环境变量设置
   - 验证密钥有效性
   - 确认API配额

2. **网络连接失败**
   - 检查网络连接
   - 验证API端点可达性
   - 配置代理设置

3. **模型不支持**
   - 检查模型名称拼写
   - 确认模型在配置文件中
   - 验证API提供商支持

### 日志调试

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 完成状态

✅ **已完成功能：**

- OpenAI兼容API集成
- 工厂模式设计
- 多模型支持（Qwen、GPT、ChatGLM）
- 异步评估任务处理
- 前端UI更新
- 配置管理系统
- 成本计算
- 错误处理
- 测试脚本

🎯 **下一步建议：**

1. 设置真实API密钥进行测试
2. 在前端界面测试完整流程
3. 根据需要调整评估提示词
4. 监控API使用量和成本
5. 收集用户反馈优化体验

---

**技术支持**: 如有问题，请检查日志文件或联系开发团队。
