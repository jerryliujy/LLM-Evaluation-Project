-- 数据集及其版本
CREATE TABLE `Dataset` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` TEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Version` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `dataset_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_version_dataset` (`dataset_id`),
  CONSTRAINT `fk_version_dataset`
    FOREIGN KEY (`dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始问题
CREATE TABLE `RawQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(512) NOT NULL,
  `url` VARCHAR(1024) DEFAULT NULL,
  `body` TEXT DEFAULT NULL,
  `vote_count` INT NOT NULL DEFAULT 0,
  `view_count` INT NOT NULL DEFAULT 0,
  `author` VARCHAR(255) DEFAULT NULL,
  `tags` JSON DEFAULT NULL,
  `issued_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_rawquestion_title` (`title`),
  INDEX `idx_rawquestion_is_deleted` (`is_deleted`),
  UNIQUE INDEX `idx_rawquestion_url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 专家表
CREATE TABLE `Expert` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_expert_name` (`name`),
  UNIQUE INDEX `idx_expert_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始回答
CREATE TABLE `RawAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `question_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `vote_count` INT NOT NULL DEFAULT 0,
  `author` VARCHAR(255) DEFAULT NULL,
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
  `content` TEXT NOT NULL,
  `source` VARCHAR(255) NOT NULL,
  `vote_count` INT DEFAULT 0,
  `author` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_expertanswer_question` (`question_id`),
  INDEX `idx_expertanswer_author` (`author`),
  INDEX `idx_expertanswer_source` (`source`),
  INDEX `idx_expertanswer_is_deleted` (`is_deleted`),
  CONSTRAINT `fk_expertanswer_rawquestion`
    FOREIGN KEY (`question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_expertanswer_expert`
    FOREIGN KEY (`author`) REFERENCES `Expert` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题及其来源
CREATE TABLE `StdQuestion` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `raw_question_id` INT NOT NULL,
  `text` TEXT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `question_type` VARCHAR(50) NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `created_by` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sq_rawq` (`raw_question_id`),
  CONSTRAINT `fk_stdquestion_rawq`
    FOREIGN KEY (`raw_question_id`) REFERENCES `RawQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准回答
CREATE TABLE `StdAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_question_id` INT NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_sa_stdq` (`std_question_id`),
  CONSTRAINT `fk_stdanswer_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `StdAnswerScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `std_answer_id` INT NOT NULL,
  `scoring_point_text` TEXT NOT NULL,
  `point_order` INT DEFAULT 0, 
  PRIMARY KEY (`id`),
  KEY `idx_sasp_stdanswer` (`std_answer_id`),
  CONSTRAINT `fk_sasp_stdanswer`
    FOREIGN KEY (`std_answer_id`) REFERENCES `StdAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dataset ↔ Std_Question 多对多
CREATE TABLE `DatasetQuestionRecord` (
  `dataset_id` INT NOT NULL,
  `std_question_id` INT NOT NULL,
  PRIMARY KEY (`dataset_id`,`std_question_id`),
  KEY `idx_dsq_dataset` (`dataset_id`),
  KEY `idx_dsq_stdq` (`std_question_id`),
  CONSTRAINT `fk_dsq_dataset`
    FOREIGN KEY (`dataset_id`) REFERENCES `Dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dsq_stdquestion`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标签与标准问题的多对多
CREATE TABLE `Tag` (
  `label` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`label`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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

-- LLM 与 LLM 回答
CREATE TABLE `LLM` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `version` VARCHAR(50) NOT NULL,
  `affiliation` VARCHAR(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LLMAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `llm_id` INT NOT NULL,
  `create_time` DATETIME NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_la_llm` (`llm_id`),
  CONSTRAINT `fk_llmanswer_llm`
    FOREIGN KEY (`llm_id`) REFERENCES `LLM` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LLMAnswerScoringPoint` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `llm_answer_id` INT NOT NULL,
  `scoring_point_text` TEXT NOT NULL,
  `point_order` INT DEFAULT 0, 
  PRIMARY KEY (`id`),
  KEY `idx_lasp_llmanswer` (`llm_answer_id`),
  CONSTRAINT `fk_lasp_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLMAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 标准问题对 LLM 回答的评估
CREATE TABLE `Evaluation` (
  `std_question_id` INT NOT NULL,
  `llm_answer_id` INT NOT NULL,
  `score` DECIMAL(5,2) DEFAULT NULL,
  `eval_method` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`std_question_id`,`llm_answer_id`),
  KEY `idx_eval_stdq` (`std_question_id`),
  KEY `idx_eval_llma` (`llm_answer_id`),
  CONSTRAINT `fk_eval_stdq`
    FOREIGN KEY (`std_question_id`) REFERENCES `StdQuestion` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_eval_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLMAnswer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
