-- 完整的数据库架构，包含多对多关系表
-- 创建日期：2025年6月5日
-- 描述：合并了基础表结构和多对多关系表的完整数据库架构

-- 用户表
CREATE TABLE `User` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('admin', 'user', 'expert') NOT NULL DEFAULT 'user',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `invite_code` VARCHAR(50) DEFAULT NULL, 
  PRIMARY KEY (`id`),
  UNIQUE INDEX `idx_user_username` (`username`),
  UNIQUE INDEX `idx_user_invite_code` (`invite_code`),
  INDEX `idx_user_role` (`role`),
  INDEX `idx_user_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 数据集
CREATE TABLE `Dataset` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version` INT NOT NULL DEFAULT 1,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `created_by` INT NOT NULL,
  `is_public` TINYINT(1) NOT NULL DEFAULT 0,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `version`),
  INDEX `idx_dataset_created_by` (`created_by`),
  INDEX `idx_dataset_public` (`is_public`),
  INDEX `idx_dataset_valid` (`is_valid`),
  CONSTRAINT `fk_dataset_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始问题
CREATE TABLE `RawQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `url` VARCHAR(255) DEFAULT NULL,
  `body` TEXT DEFAULT NULL,
  `votes` VARCHAR(20) DEFAULT NULL,
  `views` VARCHAR(20) DEFAULT NULL, -- 支持 "1.1m" 这样的格式
  `author` VARCHAR(255) DEFAULT NULL,
  `tags_json` JSON DEFAULT NULL, -- 原始JSON格式tags，用于导入时临时存储
  `issued_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_rawquestion_title` (`title`),
  INDEX `idx_rawquestion_is_deleted` (`is_deleted`),
  INDEX `idx_rawquestion_created_by` (`created_by`),
  UNIQUE INDEX `idx_rawquestion_url` (`url`),
  CONSTRAINT `fk_raw_question_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题
CREATE TABLE `StdQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `dataset_id` INT NOT NULL,  -- 当前所在的数据集ID
  `body` TEXT NOT NULL,
  `question_type` ENUM('choice', 'text') NOT NULL DEFAULT 'text',
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1,
  `previous_version_id` INT DEFAULT NULL, -- 指向前一个版本
  `original_version_id` INT NOT NULL,  -- 最初创建时的版本号
  `current_version_id` INT NOT NULL,  -- 当前所在的版本号
  PRIMARY KEY (`id`),
  INDEX `idx_stdquestion_dataset` (`dataset_id`),
  INDEX `idx_stdquestion_valid` (`is_valid`),
  INDEX `idx_stdquestion_created_by` (`created_by`),
  INDEX `idx_stdquestion_version` (`version`),
  INDEX `idx_stdquestion_original_version` (`original_version_id`),
  INDEX `idx_stdquestion_current_version` (`current_version_id`),
  CONSTRAINT `fk_stdquestion_dataset`
    FOREIGN KEY (`dataset_id`, `current_version_id`) REFERENCES `Dataset` (`id`, `version`)
    ON DELETE CASCADE ON UPDATE CASCADE,  
  CONSTRAINT `fk_stdquestion_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdquestion_previous`
    FOREIGN KEY (`previous_version_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准回答
CREATE TABLE `StdAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `answered_by` INT DEFAULT NULL,
  `answered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `version` INT NOT NULL DEFAULT 1,
  `previous_version_id` INT DEFAULT NULL, -- 指向前一个版本
  `original_version_id` INT NOT NULL,  -- 最初创建时的版本号
  `current_version_id` INT NOT NULL,  -- 当前所在的版本号
  PRIMARY KEY (`id`),
  KEY `idx_sa_stdq` (`std_question_id`),
  INDEX `idx_stdanswer_version` (`version`),
  INDEX `idx_stdanswer_valid` (`is_valid`),
  INDEX `idx_stdanswer_original_version` (`original_version_id`),
  INDEX `idx_stdanswer_current_version` (`current_version_id`),
  CONSTRAINT `fk_stdanswer_user`
    FOREIGN KEY (`answered_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_previous`
    FOREIGN KEY (`previous_version_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始回答
CREATE TABLE `RawAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `upvotes` VARCHAR(20) DEFAULT NULL,
  `answered_by` VARCHAR(255) DEFAULT NULL,
  `answered_at` DATETIME DEFAULT NULL,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_rawanswer_question` (`question_id`),
  INDEX `idx_rawanswer_is_deleted` (`is_deleted`),
  CONSTRAINT `fk_rawanswer_rawquestion`
    FOREIGN KEY (`question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 专家回答
CREATE TABLE `ExpertAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `answered_by` INT NOT NULL,
  `answered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_expertanswer_question` (`question_id`),
  INDEX `idx_expertanswer_author` (`answered_by`),
  INDEX `idx_expertanswer_is_deleted` (`is_deleted`),
  CONSTRAINT `fk_expertanswer_rawquestion`
    FOREIGN KEY (`question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_expertanswer_expert`
    FOREIGN KEY (`answered_by`) REFERENCES `User` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准答案评分点
CREATE TABLE `StdAnswerScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_answer_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `point_order` INT DEFAULT 0,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `answered_by` INT DEFAULT NULL,
  `answered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `version` INT NOT NULL DEFAULT 1,
  `previous_version_id` INT DEFAULT NULL, -- 指向前一个版本
  PRIMARY KEY (`id`),
  KEY `idx_sasp_stdanswer` (`std_answer_id`),
  INDEX `idx_sasp_version` (`version`),
  INDEX `idx_sasp_valid` (`is_valid`),
  CONSTRAINT `fk_sasp_user`
    FOREIGN KEY (`answered_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_sasp_stdanswer`
    FOREIGN KEY (`std_answer_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sasp_previous`
    FOREIGN KEY (`previous_version_id`) REFERENCES `StdAnswerScoringPoint` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== 多对多关系表 ==================

-- 标准回答与原始回答的关系表
CREATE TABLE `StdAnswerRawAnswerRecord` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_answer_id` INT NOT NULL,
  `raw_answer_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_std_raw_answer` (`std_answer_id`, `raw_answer_id`),
  KEY `idx_srar_std_answer` (`std_answer_id`),
  KEY `idx_srar_raw_answer` (`raw_answer_id`),
  KEY `idx_srar_created_by` (`created_by`),
  CONSTRAINT `fk_srar_std_answer`
    FOREIGN KEY (`std_answer_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_srar_raw_answer`
    FOREIGN KEY (`raw_answer_id`) REFERENCES `RawAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_srar_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准回答与专家回答的关系表
CREATE TABLE `StdAnswerExpertAnswerRecord` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_answer_id` INT NOT NULL,
  `expert_answer_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_std_expert_answer` (`std_answer_id`, `expert_answer_id`),
  KEY `idx_sear_std_answer` (`std_answer_id`),
  KEY `idx_sear_expert_answer` (`expert_answer_id`),
  KEY `idx_sear_created_by` (`created_by`),
  CONSTRAINT `fk_sear_std_answer`
    FOREIGN KEY (`std_answer_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sear_expert_answer`
    FOREIGN KEY (`expert_answer_id`) REFERENCES `ExpertAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sear_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题与原始问题的关系表
CREATE TABLE `StdQuestionRawQuestionRecord` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `raw_question_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_std_raw_question` (`std_question_id`, `raw_question_id`),
  KEY `idx_sqrr_std_question` (`std_question_id`),
  KEY `idx_sqrr_raw_question` (`raw_question_id`),
  KEY `idx_sqrr_created_by` (`created_by`),
  CONSTRAINT `fk_sqrr_std_question`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sqrr_raw_question`
    FOREIGN KEY (`raw_question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sqrr_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== 标签系统 ==================

-- 标签表
CREATE TABLE `Tag` (
  `label` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`label`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始问题与标签的关联表
CREATE TABLE `RawQuestionTagRecords` (
  `raw_question_id` INT NOT NULL,
  `tag_label` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`raw_question_id`,`tag_label`),
  KEY `idx_rqt_rawq` (`raw_question_id`),
  KEY `idx_rqt_tag` (`tag_label`),
  CONSTRAINT `fk_rqt_rawq`
    FOREIGN KEY (`raw_question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rqt_tag`
    FOREIGN KEY (`tag_label`) REFERENCES `Tag` (`label`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题与标签的关联表
CREATE TABLE `QuestionTagRecords` (
  `std_question_id` INT NOT NULL,
  `tag_label` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`std_question_id`,`tag_label`),
  KEY `idx_sqt_stdq` (`std_question_id`),
  KEY `idx_sqt_tag` (`tag_label`),
  CONSTRAINT `fk_sqt_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_sqt_tag`
    FOREIGN KEY (`tag_label`) REFERENCES `Tag` (`label`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== LLM评估系统 ==================

-- LLM表
CREATE TABLE `LLM` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `display_name` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(100) NOT NULL,
  `api_endpoint` VARCHAR(500) DEFAULT NULL,
  `default_temperature` DECIMAL(3,2) DEFAULT 0.7,
  `max_tokens` INT DEFAULT 4000,
  `top_k` INT DEFAULT 50,
  `enable_reasoning` TINYINT(1) NOT NULL DEFAULT 0,
  `cost_per_1k_tokens` DECIMAL(8,6) DEFAULT 0.0006,
  `description` TEXT DEFAULT NULL,
  `version` VARCHAR(50) DEFAULT NULL,
  `affiliation` VARCHAR(100) DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `idx_llm_name` (`name`),
  INDEX `idx_llm_provider` (`provider`),
  INDEX `idx_llm_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LLM评测任务表
CREATE TABLE `LLMEvaluationTask` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `dataset_id` INT NOT NULL,
  `dataset_version` INT NOT NULL,
  `created_by` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` ENUM('config_params', 'config_prompts', 'generating_answers', 'evaluating_answers', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'config_params',
  `progress` INT NOT NULL DEFAULT 0,
  `score` DECIMAL(5,2) DEFAULT NULL,
  `total_questions` INT NOT NULL DEFAULT 0,
  `completed_questions` INT NOT NULL DEFAULT 0,
  `failed_questions` INT NOT NULL DEFAULT 0,  
  `model_id` INT NOT NULL,
  `api_key_hash` VARCHAR(255) DEFAULT NULL,
  `system_prompt` TEXT DEFAULT NULL,
  `choice_system_prompt` TEXT DEFAULT NULL,
  `text_system_prompt` TEXT DEFAULT NULL,
  `choice_evaluation_prompt` TEXT DEFAULT NULL,
  `text_evaluation_prompt` TEXT DEFAULT NULL,
  `temperature` DECIMAL(3,2) DEFAULT 0.7,
  `max_tokens` INT DEFAULT 2000,
  `top_k` INT DEFAULT 50,
  `enable_reasoning` TINYINT(1) NOT NULL DEFAULT 0,
  `evaluation_prompt` TEXT DEFAULT NULL,
  `started_at` DATETIME DEFAULT NULL,
  `completed_at` DATETIME DEFAULT NULL,
  `error_message` TEXT DEFAULT NULL,
  `result_summary` JSON DEFAULT NULL,  PRIMARY KEY (`id`),
  INDEX `idx_task_dataset` (`dataset_id`, `dataset_version`),
  INDEX `idx_task_created_by` (`created_by`),
  INDEX `idx_task_status` (`status`),
  INDEX `idx_task_created_at` (`created_at`),  
  INDEX `idx_task_model` (`model_id`),
  CONSTRAINT `fk_task_dataset`
    FOREIGN KEY (`dataset_id`, `dataset_version`) REFERENCES `Dataset` (`id`, `version`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_task_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_task_llm`
    FOREIGN KEY (`model_id`) REFERENCES `LLM` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LLM回答
CREATE TABLE `LLMAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `llm_id` INT DEFAULT NULL,
  `task_id` INT DEFAULT NULL,
  `std_question_id` INT DEFAULT NULL,
  `prompt_used` TEXT DEFAULT NULL,
  `answer` TEXT DEFAULT NULL,
  `answered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_la_llm` (`llm_id`),
  KEY `idx_la_task` (`task_id`),
  KEY `idx_la_question` (`std_question_id`),
  INDEX `idx_la_answered_at` (`answered_at`),
  INDEX `idx_la_valid` (`is_valid`),
  CONSTRAINT `fk_llmanswer_llm`
    FOREIGN KEY (`llm_id`) REFERENCES `LLM` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_llmanswer_task`
    FOREIGN KEY (`task_id`) REFERENCES `LLMEvaluationTask` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_llmanswer_question`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题对LLM回答的评估
CREATE TABLE `Evaluation` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `llm_answer_id` INT NOT NULL,
  `score` DECIMAL(5,2) DEFAULT NULL,
  `evaluator_type` ENUM('user', 'llm') NOT NULL,
  `evaluator_id` INT NOT NULL, -- 用户ID或LLM ID
  `evaluation_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `notes` TEXT DEFAULT NULL,
  `reasoning` TEXT DEFAULT NULL, -- 评估理由
  `evaluation_prompt` TEXT DEFAULT NULL, -- 使用的评估提示词
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_eval_unique` (`std_question_id`, `llm_answer_id`, `evaluator_type`, `evaluator_id`),
  KEY `idx_eval_stdq` (`std_question_id`),
  KEY `idx_eval_llma` (`llm_answer_id`),
  KEY `idx_eval_type` (`evaluator_type`),
  KEY `idx_eval_evaluator` (`evaluator_id`),
  INDEX `idx_eval_time` (`evaluation_time`),
  CONSTRAINT `fk_eval_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_eval_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLMAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== 版本管理系统 ==================

-- 数据集版本工作表
CREATE TABLE `DatasetVersionWork` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `dataset_id` INT NOT NULL,
  `current_version` INT NOT NULL,
  `target_version` INT NOT NULL,
  `work_status` ENUM('in_progress', 'completed', 'cancelled') NOT NULL DEFAULT 'in_progress',
  `work_description` TEXT DEFAULT NULL,
  `created_by` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` DATETIME DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_dataset_version_work_dataset` (`dataset_id`, `current_version`),
  INDEX `idx_dataset_version_work_status` (`work_status`),
  INDEX `idx_dataset_version_work_created_by` (`created_by`),
  INDEX `idx_dataset_version_work_created_at` (`created_at`),
  CONSTRAINT `fk_dataset_version_work_dataset`
    FOREIGN KEY (`dataset_id`, `current_version`) REFERENCES `Dataset` (`id`, `version`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dataset_version_work_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本工作表中的标准问题
CREATE TABLE `VersionStdQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_work_id` INT NOT NULL,
  `original_question_id` INT DEFAULT NULL,
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
  `is_new` TINYINT(1) NOT NULL DEFAULT 0,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `modified_body` TEXT DEFAULT NULL,
  `modified_question_type` ENUM('choice', 'text') DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_version_std_question_work` (`version_work_id`),
  INDEX `idx_version_std_question_original` (`original_question_id`),
  CONSTRAINT `fk_version_std_question_work`
    FOREIGN KEY (`version_work_id`) REFERENCES `DatasetVersionWork` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_std_question_original`
    FOREIGN KEY (`original_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本工作表中的标准答案
CREATE TABLE `VersionStdAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_work_id` INT NOT NULL,
  `original_answer_id` INT DEFAULT NULL,
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `is_new` TINYINT(1) NOT NULL DEFAULT 1,
  `modified_answer` TEXT DEFAULT NULL,
  `modified_answered_by` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_version_std_answer_work` (`version_work_id`),
  INDEX `idx_version_std_answer_original` (`original_answer_id`),
  CONSTRAINT `fk_version_std_answer_work`
    FOREIGN KEY (`version_work_id`) REFERENCES `DatasetVersionWork` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_std_answer_original`
    FOREIGN KEY (`original_answer_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_std_answer_user`
    FOREIGN KEY (`modified_answered_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本工作表中的得分点
CREATE TABLE `VersionScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_work_id` INT NOT NULL,
  `version_answer_id` INT NOT NULL,
  `original_point_id` INT DEFAULT NULL,
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `is_new` TINYINT(1) NOT NULL DEFAULT 1,
  `modified_answer` TEXT DEFAULT NULL,
  `modified_point_order` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_version_scoring_point_work` (`version_work_id`),
  INDEX `idx_version_scoring_point_answer` (`version_answer_id`),
  INDEX `idx_version_scoring_point_original` (`original_point_id`),
  CONSTRAINT `fk_version_scoring_point_work`
    FOREIGN KEY (`version_work_id`) REFERENCES `DatasetVersionWork` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_scoring_point_answer`
    FOREIGN KEY (`version_answer_id`) REFERENCES `VersionStdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_scoring_point_original`
    FOREIGN KEY (`original_point_id`) REFERENCES `StdAnswerScoringPoint` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本工作表中的标签
CREATE TABLE `VersionTag` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_work_id` INT NOT NULL,
  `version_question_id` INT NOT NULL,
  `tag_label` VARCHAR(100) NOT NULL,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `is_new` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_version_tag_work` (`version_work_id`),
  INDEX `idx_version_tag_question` (`version_question_id`),
  INDEX `idx_version_tag_label` (`tag_label`),
  CONSTRAINT `fk_version_tag_work`
    FOREIGN KEY (`version_work_id`) REFERENCES `DatasetVersionWork` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_tag_question`
    FOREIGN KEY (`version_question_id`) REFERENCES `VersionStdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_version_tag_label`
    FOREIGN KEY (`tag_label`) REFERENCES `Tag` (`label`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== 初始化数据 ==================

-- 插入支持的LLM模型
-- 插入初始LLM模型数据
INSERT INTO `LLM` (`name`, `display_name`, `provider`, `api_endpoint`, `max_tokens`, `default_temperature`, `top_k`, `enable_reasoning`, `cost_per_1k_tokens`, `description`, `version`, `affiliation`, `is_active`) VALUES
('qwen-turbo', '通义千问Turbo', 'Alibaba Cloud', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 8000, 0.7, 50, 0, 0.0006, '通义千问Turbo模型，快速响应，适合日常对话', '2025-04-28', 'Alibaba', 1);
