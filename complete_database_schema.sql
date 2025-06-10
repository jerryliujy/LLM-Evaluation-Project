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
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `created_by` INT NOT NULL,
  `is_public` TINYINT(1) NOT NULL DEFAULT 0,
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `version` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  INDEX `idx_dataset_created_by` (`created_by`),
  INDEX `idx_dataset_public` (`is_public`),
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
  `body` TEXT NOT NULL,
  `question_type` ENUM('choice', 'text') NOT NULL DEFAULT 'text',
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` INT DEFAULT NULL,
  `previous_version_id` INT DEFAULT NULL, -- 指向前一个版本
  `original_dataset_id` INT NOT NULL, -- 原始数据集ID（必须字段）
  `current_dataset_id` INT NOT NULL, -- 当前数据集ID（必须字段）
  PRIMARY KEY (`id`),
  INDEX `idx_stdquestion_valid` (`is_valid`),
  INDEX `idx_stdquestion_created_by` (`created_by`),
  INDEX `idx_stdquestion_original_dataset` (`original_dataset_id`),
  INDEX `idx_stdquestion_current_dataset` (`current_dataset_id`),
  INDEX `idx_stdquestion_dataset_range` (`original_dataset_id`, `current_dataset_id`),
  CONSTRAINT `fk_stdquestion_user`
    FOREIGN KEY (`created_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdquestion_previous`
    FOREIGN KEY (`previous_version_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdquestion_original_dataset`
    FOREIGN KEY (`original_dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_stdquestion_current_dataset`
    FOREIGN KEY (`current_dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准回答
CREATE TABLE `StdAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `answered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `answered_by` INT DEFAULT NULL,
  `previous_version_id` INT DEFAULT NULL, -- 指向前一个版本
  `original_dataset_id` INT NOT NULL, -- 原始数据集ID（必须字段）
  `current_dataset_id` INT NOT NULL, -- 当前数据集ID（必须字段）
  PRIMARY KEY (`id`),
  KEY `idx_sa_stdq` (`std_question_id`),
  INDEX `idx_stdanswer_valid` (`is_valid`),
  INDEX `idx_stdanswer_answered_by` (`answered_by`),
  INDEX `idx_stdanswer_original_dataset` (`original_dataset_id`),
  INDEX `idx_stdanswer_current_dataset` (`current_dataset_id`),
  INDEX `idx_stdanswer_dataset_range` (`original_dataset_id`, `current_dataset_id`),
  CONSTRAINT `fk_stdanswer_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_user`
    FOREIGN KEY (`answered_by`) REFERENCES `User` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_previous`
    FOREIGN KEY (`previous_version_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_original_dataset`
    FOREIGN KEY (`original_dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_stdanswer_current_dataset`
    FOREIGN KEY (`current_dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
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
  `previous_version_id` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sasp_stdanswer` (`std_answer_id`),
  INDEX `idx_sasp_valid` (`is_valid`),
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
  `version` VARCHAR(50) NOT NULL,
  `affiliation` VARCHAR(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LLM回答
CREATE TABLE `LLMAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `llm_id` INT NOT NULL,
  `answered_at` DATETIME NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_la_llm` (`llm_id`),
  CONSTRAINT `fk_llmanswer_llm`
    FOREIGN KEY (`llm_id`) REFERENCES `LLM` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LLM回答评分点
CREATE TABLE `LLMAnswerScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `llm_answer_id` INT NOT NULL,
  `answer` TEXT NOT NULL,
  `point_order` INT DEFAULT 0, 
  PRIMARY KEY (`id`),
  KEY `idx_lasp_llmanswer` (`llm_answer_id`),
  CONSTRAINT `fk_lasp_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLMAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题对LLM回答的评估
CREATE TABLE `Evaluation` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `llm_answer_id` INT NOT NULL,
  `score` DECIMAL(5,2) DEFAULT NULL,
  `evaluator_type` ENUM('user', 'llm') NOT NULL,
  `evaluator_id` INT DEFAULT NULL, -- 用户ID或LLM ID
  `evaluation_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `notes` TEXT DEFAULT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_eval_unique` (`std_question_id`, `llm_answer_id`, `evaluator_type`, `evaluator_id`),
  KEY `idx_eval_stdq` (`std_question_id`),
  KEY `idx_eval_llma` (`llm_answer_id`),
  KEY `idx_eval_type` (`evaluator_type`),
  KEY `idx_eval_evaluator` (`evaluator_id`),
  CONSTRAINT `fk_eval_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_eval_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLMAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ================== 版本管理系统 ==================

-- 数据集版本表
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本标准问题工作表
CREATE TABLE `VersionStdQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_id` INT NOT NULL,
  `original_question_id` INT DEFAULT NULL, -- 引用原始问题ID
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0, -- 是否修改
  `is_new` TINYINT(1) NOT NULL DEFAULT 0, -- 是否新创建
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0, -- 是否删除
  `modified_body` TEXT DEFAULT NULL, -- 修改后的问题内容
  `modified_question_type` ENUM('choice', 'text') DEFAULT NULL, -- 修改后的问题类型
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本标准答案工作表
CREATE TABLE `VersionStdAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_id` INT NOT NULL,
  `version_question_id` INT NOT NULL, -- 关联版本问题
  `original_answer_id` INT DEFAULT NULL, -- 引用原始答案ID
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0, -- 是否修改
  `is_new` TINYINT(1) NOT NULL DEFAULT 1, -- 是否新创建
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0, -- 是否删除
  `modified_answer` TEXT DEFAULT NULL, -- 修改后的答案内容
  `modified_answered_by` INT DEFAULT NULL, -- 修改后的回答者
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 版本评分点工作表
CREATE TABLE `VersionScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version_id` INT NOT NULL,
  `version_answer_id` INT NOT NULL, -- 关联版本答案
  `original_point_id` INT DEFAULT NULL, -- 引用原始评分点ID
  `is_modified` TINYINT(1) NOT NULL DEFAULT 0, -- 是否修改
  `is_new` TINYINT(1) NOT NULL DEFAULT 1, -- 是否新创建
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0, -- 是否删除
  `modified_answer` TEXT DEFAULT NULL, -- 修改后的评分点内容
  `modified_point_order` INT DEFAULT NULL, -- 修改后的顺序
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

