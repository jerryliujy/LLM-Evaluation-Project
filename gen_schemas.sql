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
  `title` VARCHAR(255) NOT NULL,
  `url` VARCHAR(255) DEFAULT NULL,
  `body` TEXT NOT NULL,
  `vote_count` INT NOT NULL DEFAULT 0,
  `view_count` INT NOT NULL DEFAULT 0,
  `author` VARCHAR(100) DEFAULT NULL,
  `issued_at` DATETIME NOT NULL,
  `created_at` DATETIME NOT NULL,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`)
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
    FOREIGN KEY (`raw_question_id`) REFERENCES `Raw_Question` (`id`)
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
    FOREIGN KEY (`std_question_id`) REFERENCES `Std_Question` (`id`)
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
    FOREIGN KEY (`std_answer_id`) REFERENCES `Std_Answer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 专家及专家回答
CREATE TABLE `Expert` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `password` VARCHAR(100) DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ExpertAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `expert_id` INT NOT NULL,
  `std_answer_id` INT DEFAULT NULL, 
  `text` TEXT NOT NULL,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_ea_expert` (`expert_id`),
  KEY `idx_ea_std_answer` (`std_answer_id`), 
  CONSTRAINT `fk_expertanswer_expert`
    FOREIGN KEY (`expert_id`) REFERENCES `Expert` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_expertanswer_stdanswer` 
    FOREIGN KEY (`std_answer_id`) REFERENCES `Std_Answer` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 原始回答（需要在专家回答之后被创建，因为原始回答和专家回答是多对一的关系）
CREATE TABLE `RawAnswer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `raw_question_id` INT NOT NULL,
  `text` TEXT NOT NULL,
  `like_number` INT NOT NULL DEFAULT 0,
  `hate_number` INT NOT NULL DEFAULT 0,
  `is_valid` TINYINT(1) NOT NULL DEFAULT 1,
  `expert_answer_id` INT DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ra_raw_question` (`raw_question_id`),
  KEY `idx_ra_expert_answer` (`expert_answer_id`),
  CONSTRAINT `fk_rawanswer_rawq`
    FOREIGN KEY (`raw_question_id`) REFERENCES `Raw_Question` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rawanswer_expertanswer`
    FOREIGN KEY (`expert_answer_id`) REFERENCES `Expert_Answer` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
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
    FOREIGN KEY (`std_question_id`) REFERENCES `Std_Question` (`id`)
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
    FOREIGN KEY (`std_question_id`) REFERENCES `Std_Question` (`id`)
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
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLM_Answer` (`id`)
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
    FOREIGN KEY (`std_question_id`) REFERENCES `Std_Question` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_eval_llmanswer`
    FOREIGN KEY (`llm_answer_id`) REFERENCES `LLM_Answer` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
