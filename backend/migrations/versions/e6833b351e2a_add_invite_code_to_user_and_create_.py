"""Add invite_code to User and create ExpertTask table

Revision ID: e6833b351e2a
Revises: 
Create Date: 2025-06-05 21:07:45.449293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'e6833b351e2a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_srar_raw_answer', table_name='StdAnswerRawAnswerRecord')
    op.drop_index('idx_srar_std_answer', table_name='StdAnswerRawAnswerRecord')
    op.drop_index('uk_std_raw_answer', table_name='StdAnswerRawAnswerRecord')
    op.drop_table('StdAnswerRawAnswerRecord')
    op.drop_index('idx_eval_llma', table_name='Evaluation')
    op.drop_index('idx_eval_stdq', table_name='Evaluation')
    op.drop_table('Evaluation')
    op.drop_index('idx_sear_expert_answer', table_name='StdAnswerExpertAnswerRecord')
    op.drop_index('idx_sear_std_answer', table_name='StdAnswerExpertAnswerRecord')
    op.drop_index('uk_std_expert_answer', table_name='StdAnswerExpertAnswerRecord')
    op.drop_table('StdAnswerExpertAnswerRecord')
    op.drop_index('idx_lasp_llmanswer', table_name='LLMAnswerScoringPoint')
    op.drop_table('LLMAnswerScoringPoint')
    op.drop_table('LLM')
    op.drop_index('idx_la_llm', table_name='LLMAnswer')
    op.drop_table('LLMAnswer')
    op.drop_index('idx_sqrr_raw_question', table_name='StdQuestionRawQuestionRecord')
    op.drop_index('idx_sqrr_std_question', table_name='StdQuestionRawQuestionRecord')
    op.drop_index('uk_std_raw_question', table_name='StdQuestionRawQuestionRecord')
    op.drop_table('StdQuestionRawQuestionRecord')
    op.alter_column('Dataset', 'is_public',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True,
               existing_server_default=sa.text("'0'"))
    op.alter_column('Dataset', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_index('idx_dataset_created_by', table_name='Dataset')
    op.drop_index('idx_dataset_public', table_name='Dataset')
    op.create_index(op.f('ix_Dataset_id'), 'Dataset', ['id'], unique=False)
    op.drop_constraint('fk_dataset_user', 'Dataset', type_='foreignkey')
    op.create_foreign_key(None, 'Dataset', 'User', ['created_by'], ['id'])
    op.alter_column('ExpertAnswer', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_index('idx_expertanswer_author', table_name='ExpertAnswer')
    op.drop_index('idx_expertanswer_is_deleted', table_name='ExpertAnswer')
    op.drop_index('idx_expertanswer_question', table_name='ExpertAnswer')
    op.create_index(op.f('ix_ExpertAnswer_author'), 'ExpertAnswer', ['author'], unique=False)
    op.create_index(op.f('ix_ExpertAnswer_id'), 'ExpertAnswer', ['id'], unique=False)
    op.create_index(op.f('ix_ExpertAnswer_is_deleted'), 'ExpertAnswer', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_ExpertAnswer_question_id'), 'ExpertAnswer', ['question_id'], unique=False)
    op.drop_constraint('fk_expertanswer_rawquestion', 'ExpertAnswer', type_='foreignkey')
    op.drop_constraint('fk_expertanswer_expert', 'ExpertAnswer', type_='foreignkey')
    op.create_foreign_key(None, 'ExpertAnswer', 'User', ['author'], ['id'])
    op.create_foreign_key(None, 'ExpertAnswer', 'RawQuestion', ['question_id'], ['id'])
    op.drop_index('idx_sqt_stdq', table_name='QuestionTagRecords')
    op.drop_index('idx_sqt_tag', table_name='QuestionTagRecords')
    op.drop_constraint('fk_sqt_tag', 'QuestionTagRecords', type_='foreignkey')
    op.drop_constraint('fk_sqt_stdq', 'QuestionTagRecords', type_='foreignkey')
    op.create_foreign_key(None, 'QuestionTagRecords', 'StdQuestion', ['std_question_id'], ['id'])
    op.create_foreign_key(None, 'QuestionTagRecords', 'Tag', ['tag_label'], ['label'])
    op.drop_index('idx_rawanswer_is_deleted', table_name='RawAnswer')
    op.drop_index('idx_rawanswer_question', table_name='RawAnswer')
    op.create_index(op.f('ix_RawAnswer_id'), 'RawAnswer', ['id'], unique=False)
    op.create_index(op.f('ix_RawAnswer_is_deleted'), 'RawAnswer', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_RawAnswer_question_id'), 'RawAnswer', ['question_id'], unique=False)
    op.drop_constraint('fk_rawanswer_rawquestion', 'RawAnswer', type_='foreignkey')
    op.create_foreign_key(None, 'RawAnswer', 'RawQuestion', ['question_id'], ['id'])
    op.alter_column('RawQuestion', 'title',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=191),
               existing_nullable=False)
    op.alter_column('RawQuestion', 'url',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.String(length=191),
               existing_nullable=True)
    op.alter_column('RawQuestion', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('RawQuestion', 'created_by',
               existing_type=mysql.INTEGER(),
               nullable=True)
    op.drop_index('idx_rawquestion_is_deleted', table_name='RawQuestion')
    op.drop_index('idx_rawquestion_title', table_name='RawQuestion')
    op.create_index(op.f('ix_RawQuestion_created_by'), 'RawQuestion', ['created_by'], unique=False)
    op.create_index(op.f('ix_RawQuestion_id'), 'RawQuestion', ['id'], unique=False)
    op.create_index(op.f('ix_RawQuestion_is_deleted'), 'RawQuestion', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_RawQuestion_title'), 'RawQuestion', ['title'], unique=False)
    op.drop_constraint('fk_raw_question_user', 'RawQuestion', type_='foreignkey')
    op.create_foreign_key(None, 'RawQuestion', 'User', ['created_by'], ['id'])
    op.drop_index('idx_rqt_rawq', table_name='RawQuestionTagRecords')
    op.drop_index('idx_rqt_tag', table_name='RawQuestionTagRecords')
    op.drop_constraint('fk_rqt_tag', 'RawQuestionTagRecords', type_='foreignkey')
    op.drop_constraint('fk_rqt_rawq', 'RawQuestionTagRecords', type_='foreignkey')
    op.create_foreign_key(None, 'RawQuestionTagRecords', 'Tag', ['tag_label'], ['label'])
    op.create_foreign_key(None, 'RawQuestionTagRecords', 'RawQuestion', ['raw_question_id'], ['id'])
    op.alter_column('StdAnswer', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_index('idx_sa_stdq', table_name='StdAnswer')
    op.drop_index('idx_stdanswer_valid', table_name='StdAnswer')
    op.drop_index('idx_stdanswer_version', table_name='StdAnswer')
    op.create_index(op.f('ix_StdAnswer_id'), 'StdAnswer', ['id'], unique=False)
    op.create_index(op.f('ix_StdAnswer_is_valid'), 'StdAnswer', ['is_valid'], unique=False)
    op.create_index(op.f('ix_StdAnswer_std_question_id'), 'StdAnswer', ['std_question_id'], unique=False)
    op.create_index(op.f('ix_StdAnswer_version'), 'StdAnswer', ['version'], unique=False)
    op.drop_constraint('fk_stdanswer_previous', 'StdAnswer', type_='foreignkey')
    op.drop_constraint('fk_stdanswer_stdq', 'StdAnswer', type_='foreignkey')
    op.create_foreign_key(None, 'StdAnswer', 'StdAnswer', ['previous_version_id'], ['id'])
    op.create_foreign_key(None, 'StdAnswer', 'StdQuestion', ['std_question_id'], ['id'])
    op.alter_column('StdAnswerScoringPoint', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_index('idx_sasp_stdanswer', table_name='StdAnswerScoringPoint')
    op.drop_index('idx_sasp_valid', table_name='StdAnswerScoringPoint')
    op.drop_index('idx_sasp_version', table_name='StdAnswerScoringPoint')
    op.create_index(op.f('ix_StdAnswerScoringPoint_id'), 'StdAnswerScoringPoint', ['id'], unique=False)
    op.create_index(op.f('ix_StdAnswerScoringPoint_is_valid'), 'StdAnswerScoringPoint', ['is_valid'], unique=False)
    op.create_index(op.f('ix_StdAnswerScoringPoint_std_answer_id'), 'StdAnswerScoringPoint', ['std_answer_id'], unique=False)
    op.create_index(op.f('ix_StdAnswerScoringPoint_version'), 'StdAnswerScoringPoint', ['version'], unique=False)
    op.drop_constraint('fk_sasp_stdanswer', 'StdAnswerScoringPoint', type_='foreignkey')
    op.drop_constraint('fk_sasp_previous', 'StdAnswerScoringPoint', type_='foreignkey')
    op.create_foreign_key(None, 'StdAnswerScoringPoint', 'StdAnswerScoringPoint', ['previous_version_id'], ['id'])
    op.create_foreign_key(None, 'StdAnswerScoringPoint', 'StdAnswer', ['std_answer_id'], ['id'])
    op.add_column('StdQuestion', sa.Column('raw_question_id', sa.Integer(), nullable=False))
    op.alter_column('StdQuestion', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_index('idx_stdquestion_dataset', table_name='StdQuestion')
    op.drop_index('idx_stdquestion_valid', table_name='StdQuestion')
    op.drop_index('idx_stdquestion_version', table_name='StdQuestion')
    op.create_index(op.f('ix_StdQuestion_dataset_id'), 'StdQuestion', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_StdQuestion_id'), 'StdQuestion', ['id'], unique=False)
    op.create_index(op.f('ix_StdQuestion_is_valid'), 'StdQuestion', ['is_valid'], unique=False)
    op.create_index(op.f('ix_StdQuestion_raw_question_id'), 'StdQuestion', ['raw_question_id'], unique=False)
    op.create_index(op.f('ix_StdQuestion_version'), 'StdQuestion', ['version'], unique=False)
    op.drop_constraint('fk_stdquestion_dataset', 'StdQuestion', type_='foreignkey')
    op.drop_constraint('fk_stdquestion_previous', 'StdQuestion', type_='foreignkey')
    op.create_foreign_key(None, 'StdQuestion', 'RawQuestion', ['raw_question_id'], ['id'])
    op.create_foreign_key(None, 'StdQuestion', 'Dataset', ['dataset_id'], ['id'])
    op.create_foreign_key(None, 'StdQuestion', 'StdQuestion', ['previous_version_id'], ['id'])
    op.add_column('User', sa.Column('invite_code', sa.String(length=36), nullable=True))
    op.drop_index('idx_user_active', table_name='User')
    op.drop_index('idx_user_role', table_name='User')
    op.drop_index('idx_user_username', table_name='User')
    op.drop_index('username', table_name='User')
    op.create_index(op.f('ix_User_id'), 'User', ['id'], unique=False)
    op.create_index(op.f('ix_User_invite_code'), 'User', ['invite_code'], unique=True)
    op.create_index(op.f('ix_User_username'), 'User', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_User_username'), table_name='User')
    op.drop_index(op.f('ix_User_invite_code'), table_name='User')
    op.drop_index(op.f('ix_User_id'), table_name='User')
    op.create_index('username', 'User', ['username'], unique=True)
    op.create_index('idx_user_username', 'User', ['username'], unique=True)
    op.create_index('idx_user_role', 'User', ['role'], unique=False)
    op.create_index('idx_user_active', 'User', ['is_active'], unique=False)
    op.drop_column('User', 'invite_code')
    op.drop_constraint(None, 'StdQuestion', type_='foreignkey')
    op.drop_constraint(None, 'StdQuestion', type_='foreignkey')
    op.drop_constraint(None, 'StdQuestion', type_='foreignkey')
    op.create_foreign_key('fk_stdquestion_previous', 'StdQuestion', 'StdQuestion', ['previous_version_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('fk_stdquestion_dataset', 'StdQuestion', 'Dataset', ['dataset_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_StdQuestion_version'), table_name='StdQuestion')
    op.drop_index(op.f('ix_StdQuestion_raw_question_id'), table_name='StdQuestion')
    op.drop_index(op.f('ix_StdQuestion_is_valid'), table_name='StdQuestion')
    op.drop_index(op.f('ix_StdQuestion_id'), table_name='StdQuestion')
    op.drop_index(op.f('ix_StdQuestion_dataset_id'), table_name='StdQuestion')
    op.create_index('idx_stdquestion_version', 'StdQuestion', ['version'], unique=False)
    op.create_index('idx_stdquestion_valid', 'StdQuestion', ['is_valid'], unique=False)
    op.create_index('idx_stdquestion_dataset', 'StdQuestion', ['dataset_id'], unique=False)
    op.alter_column('StdQuestion', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_column('StdQuestion', 'raw_question_id')
    op.drop_constraint(None, 'StdAnswerScoringPoint', type_='foreignkey')
    op.drop_constraint(None, 'StdAnswerScoringPoint', type_='foreignkey')
    op.create_foreign_key('fk_sasp_previous', 'StdAnswerScoringPoint', 'StdAnswerScoringPoint', ['previous_version_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('fk_sasp_stdanswer', 'StdAnswerScoringPoint', 'StdAnswer', ['std_answer_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_StdAnswerScoringPoint_version'), table_name='StdAnswerScoringPoint')
    op.drop_index(op.f('ix_StdAnswerScoringPoint_std_answer_id'), table_name='StdAnswerScoringPoint')
    op.drop_index(op.f('ix_StdAnswerScoringPoint_is_valid'), table_name='StdAnswerScoringPoint')
    op.drop_index(op.f('ix_StdAnswerScoringPoint_id'), table_name='StdAnswerScoringPoint')
    op.create_index('idx_sasp_version', 'StdAnswerScoringPoint', ['version'], unique=False)
    op.create_index('idx_sasp_valid', 'StdAnswerScoringPoint', ['is_valid'], unique=False)
    op.create_index('idx_sasp_stdanswer', 'StdAnswerScoringPoint', ['std_answer_id'], unique=False)
    op.alter_column('StdAnswerScoringPoint', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_constraint(None, 'StdAnswer', type_='foreignkey')
    op.drop_constraint(None, 'StdAnswer', type_='foreignkey')
    op.create_foreign_key('fk_stdanswer_stdq', 'StdAnswer', 'StdQuestion', ['std_question_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key('fk_stdanswer_previous', 'StdAnswer', 'StdAnswer', ['previous_version_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.drop_index(op.f('ix_StdAnswer_version'), table_name='StdAnswer')
    op.drop_index(op.f('ix_StdAnswer_std_question_id'), table_name='StdAnswer')
    op.drop_index(op.f('ix_StdAnswer_is_valid'), table_name='StdAnswer')
    op.drop_index(op.f('ix_StdAnswer_id'), table_name='StdAnswer')
    op.create_index('idx_stdanswer_version', 'StdAnswer', ['version'], unique=False)
    op.create_index('idx_stdanswer_valid', 'StdAnswer', ['is_valid'], unique=False)
    op.create_index('idx_sa_stdq', 'StdAnswer', ['std_question_id'], unique=False)
    op.alter_column('StdAnswer', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_constraint(None, 'RawQuestionTagRecords', type_='foreignkey')
    op.drop_constraint(None, 'RawQuestionTagRecords', type_='foreignkey')
    op.create_foreign_key('fk_rqt_rawq', 'RawQuestionTagRecords', 'RawQuestion', ['raw_question_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key('fk_rqt_tag', 'RawQuestionTagRecords', 'Tag', ['tag_label'], ['label'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_index('idx_rqt_tag', 'RawQuestionTagRecords', ['tag_label'], unique=False)
    op.create_index('idx_rqt_rawq', 'RawQuestionTagRecords', ['raw_question_id'], unique=False)
    op.drop_constraint(None, 'RawQuestion', type_='foreignkey')
    op.create_foreign_key('fk_raw_question_user', 'RawQuestion', 'User', ['created_by'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_RawQuestion_title'), table_name='RawQuestion')
    op.drop_index(op.f('ix_RawQuestion_is_deleted'), table_name='RawQuestion')
    op.drop_index(op.f('ix_RawQuestion_id'), table_name='RawQuestion')
    op.drop_index(op.f('ix_RawQuestion_created_by'), table_name='RawQuestion')
    op.create_index('idx_rawquestion_title', 'RawQuestion', ['title'], unique=False)
    op.create_index('idx_rawquestion_is_deleted', 'RawQuestion', ['is_deleted'], unique=False)
    op.alter_column('RawQuestion', 'created_by',
               existing_type=mysql.INTEGER(),
               nullable=False)
    op.alter_column('RawQuestion', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('RawQuestion', 'url',
               existing_type=sa.String(length=191),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=True)
    op.alter_column('RawQuestion', 'title',
               existing_type=sa.String(length=191),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)
    op.drop_constraint(None, 'RawAnswer', type_='foreignkey')
    op.create_foreign_key('fk_rawanswer_rawquestion', 'RawAnswer', 'RawQuestion', ['question_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_RawAnswer_question_id'), table_name='RawAnswer')
    op.drop_index(op.f('ix_RawAnswer_is_deleted'), table_name='RawAnswer')
    op.drop_index(op.f('ix_RawAnswer_id'), table_name='RawAnswer')
    op.create_index('idx_rawanswer_question', 'RawAnswer', ['question_id'], unique=False)
    op.create_index('idx_rawanswer_is_deleted', 'RawAnswer', ['is_deleted'], unique=False)
    op.drop_constraint(None, 'QuestionTagRecords', type_='foreignkey')
    op.drop_constraint(None, 'QuestionTagRecords', type_='foreignkey')
    op.create_foreign_key('fk_sqt_stdq', 'QuestionTagRecords', 'StdQuestion', ['std_question_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key('fk_sqt_tag', 'QuestionTagRecords', 'Tag', ['tag_label'], ['label'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_index('idx_sqt_tag', 'QuestionTagRecords', ['tag_label'], unique=False)
    op.create_index('idx_sqt_stdq', 'QuestionTagRecords', ['std_question_id'], unique=False)
    op.drop_constraint(None, 'ExpertAnswer', type_='foreignkey')
    op.drop_constraint(None, 'ExpertAnswer', type_='foreignkey')
    op.create_foreign_key('fk_expertanswer_expert', 'ExpertAnswer', 'User', ['author'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key('fk_expertanswer_rawquestion', 'ExpertAnswer', 'RawQuestion', ['question_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_ExpertAnswer_question_id'), table_name='ExpertAnswer')
    op.drop_index(op.f('ix_ExpertAnswer_is_deleted'), table_name='ExpertAnswer')
    op.drop_index(op.f('ix_ExpertAnswer_id'), table_name='ExpertAnswer')
    op.drop_index(op.f('ix_ExpertAnswer_author'), table_name='ExpertAnswer')
    op.create_index('idx_expertanswer_question', 'ExpertAnswer', ['question_id'], unique=False)
    op.create_index('idx_expertanswer_is_deleted', 'ExpertAnswer', ['is_deleted'], unique=False)
    op.create_index('idx_expertanswer_author', 'ExpertAnswer', ['author'], unique=False)
    op.alter_column('ExpertAnswer', 'created_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_constraint(None, 'Dataset', type_='foreignkey')
    op.create_foreign_key('fk_dataset_user', 'Dataset', 'User', ['created_by'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_index(op.f('ix_Dataset_id'), table_name='Dataset')
    op.create_index('idx_dataset_public', 'Dataset', ['is_public'], unique=False)
    op.create_index('idx_dataset_created_by', 'Dataset', ['created_by'], unique=False)
    op.alter_column('Dataset', 'create_time',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('Dataset', 'is_public',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False,
               existing_server_default=sa.text("'0'"))
    op.create_table('StdQuestionRawQuestionRecord',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('std_question_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('raw_question_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('created_by', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('notes', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['raw_question_id'], ['RawQuestion.id'], name='fk_sqrr_raw_question', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['std_question_id'], ['StdQuestion.id'], name='fk_sqrr_std_question', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('uk_std_raw_question', 'StdQuestionRawQuestionRecord', ['std_question_id', 'raw_question_id'], unique=True)
    op.create_index('idx_sqrr_std_question', 'StdQuestionRawQuestionRecord', ['std_question_id'], unique=False)
    op.create_index('idx_sqrr_raw_question', 'StdQuestionRawQuestionRecord', ['raw_question_id'], unique=False)
    op.create_table('LLMAnswer',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('llm_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('create_time', mysql.DATETIME(), nullable=False),
    sa.Column('is_valid', mysql.TINYINT(display_width=1), server_default=sa.text("'1'"), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['llm_id'], ['LLM.id'], name='fk_llmanswer_llm', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_la_llm', 'LLMAnswer', ['llm_id'], unique=False)
    op.create_table('LLM',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('version', mysql.VARCHAR(length=50), nullable=False),
    sa.Column('affiliation', mysql.VARCHAR(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('LLMAnswerScoringPoint',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('llm_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('scoring_point_text', mysql.TEXT(), nullable=False),
    sa.Column('point_order', mysql.INTEGER(), server_default=sa.text("'0'"), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['llm_answer_id'], ['LLMAnswer.id'], name='fk_lasp_llmanswer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_lasp_llmanswer', 'LLMAnswerScoringPoint', ['llm_answer_id'], unique=False)
    op.create_table('StdAnswerExpertAnswerRecord',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('std_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('expert_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('created_by', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('notes', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['expert_answer_id'], ['ExpertAnswer.id'], name='fk_sear_expert_answer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['std_answer_id'], ['StdAnswer.id'], name='fk_sear_std_answer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('uk_std_expert_answer', 'StdAnswerExpertAnswerRecord', ['std_answer_id', 'expert_answer_id'], unique=True)
    op.create_index('idx_sear_std_answer', 'StdAnswerExpertAnswerRecord', ['std_answer_id'], unique=False)
    op.create_index('idx_sear_expert_answer', 'StdAnswerExpertAnswerRecord', ['expert_answer_id'], unique=False)
    op.create_table('Evaluation',
    sa.Column('std_question_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('llm_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('score', mysql.DECIMAL(precision=5, scale=2), nullable=True),
    sa.Column('eval_by', mysql.VARCHAR(length=100), nullable=True),
    sa.ForeignKeyConstraint(['llm_answer_id'], ['LLMAnswer.id'], name='fk_eval_llmanswer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['std_question_id'], ['StdQuestion.id'], name='fk_eval_stdq', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('std_question_id', 'llm_answer_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_eval_stdq', 'Evaluation', ['std_question_id'], unique=False)
    op.create_index('idx_eval_llma', 'Evaluation', ['llm_answer_id'], unique=False)
    op.create_table('StdAnswerRawAnswerRecord',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('std_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('raw_answer_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('created_by', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('notes', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['raw_answer_id'], ['RawAnswer.id'], name='fk_srar_raw_answer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['std_answer_id'], ['StdAnswer.id'], name='fk_srar_std_answer', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('uk_std_raw_answer', 'StdAnswerRawAnswerRecord', ['std_answer_id', 'raw_answer_id'], unique=True)
    op.create_index('idx_srar_std_answer', 'StdAnswerRawAnswerRecord', ['std_answer_id'], unique=False)
    op.create_index('idx_srar_raw_answer', 'StdAnswerRawAnswerRecord', ['raw_answer_id'], unique=False)
    # ### end Alembic commands ###
