"""Initial database migration for Candidate Evaluation Platform.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-27 04:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create recruiters table
    op.create_table(
        'recruiters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('org_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_recruiters_email'), 'recruiters', ['email'], unique=True)

    # 2. Create role_profiles table
    op.create_table(
        'role_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight_consistency', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('weight_pr_quality', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('weight_review_cycles', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('weight_collaboration', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('weight_stability', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create evaluation status ENUM safely and evaluations table
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE evaluation_status_enum AS ENUM ('pending', 'active', 'completed', 'locked');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('recruiter_id', sa.Integer(), nullable=False),
        sa.Column('role_profile_id', sa.Integer(), nullable=True),
        sa.Column('candidate_name', sa.String(length=255), nullable=False),
        sa.Column('candidate_email', sa.String(length=255), nullable=False),
        sa.Column('github_username', sa.String(length=255), nullable=False),
        sa.Column('repo_owner', sa.String(length=255), nullable=False),
        sa.Column('repo_name', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'active', 'completed', 'locked', name='evaluation_status_enum', create_type=False), server_default='pending', nullable=False),
        sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('end_date > start_date', name='check_evaluations_end_after_start'),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_profile_id'], ['role_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_recruiter_id'), 'evaluations', ['recruiter_id'], unique=False)
    op.create_index(op.f('ix_evaluations_status'), 'evaluations', ['status'], unique=False)

    # 4. Create github_connections table
    op.create_table(
        'github_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('scope', sa.String(length=255), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluation_id')
    )

    # 5. Create commits table
    op.create_table(
        'commits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('sha', sa.String(length=40), nullable=False),
        sa.Column('author_login', sa.String(length=255), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('additions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_commits_eval_committed', 'commits', ['evaluation_id', 'committed_at'], unique=False)
    op.create_index(op.f('ix_commits_sha'), 'commits', ['sha'], unique=False)

    # 6. Create commit_files table
    op.create_table(
        'commit_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('commit_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['commit_id'], ['commits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_commit_files_commit_id'), 'commit_files', ['commit_id'], unique=False)

    # 7. Create pull_requests table
    op.create_table(
        'pull_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('author_login', sa.String(length=255), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('merged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('additions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pull_requests_eval_opened', 'pull_requests', ['evaluation_id', 'opened_at'], unique=False)

    # 8. Create pr_reviewers table
    op.create_table(
        'pr_reviewers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_login', sa.String(length=255), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('review_state', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pr_reviewers_pr_id'), 'pr_reviewers', ['pr_id'], unique=False)

    # 9. Create pr_comments table
    op.create_table(
        'pr_comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pr_id', sa.Integer(), nullable=False),
        sa.Column('author_login', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['pr_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pr_comments_pr_id'), 'pr_comments', ['pr_id'], unique=False)

    # 10. Create score_breakdown table
    op.create_table(
        'score_breakdown',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('raw_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('normalized_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('weight', sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_locked', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_score_breakdown_evaluation_id'), 'score_breakdown', ['evaluation_id'], unique=False)

    # 11. Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('commits_pulled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('prs_pulled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_logs_evaluation_id'), 'sync_logs', ['evaluation_id'], unique=False)

    # 12. Create PostgreSQL Trigger for score_breakdown immutability
    trigger_sql = """
    CREATE OR REPLACE FUNCTION check_score_breakdown_immutability()
    RETURNS TRIGGER AS $$
    DECLARE
        eval_status VARCHAR(50);
    BEGIN
        SELECT status INTO eval_status
        FROM evaluations
        WHERE id = OLD.evaluation_id;

        IF eval_status = 'locked' THEN
            RAISE EXCEPTION 'Cannot modify or delete score_breakdown rows for a locked evaluation (evaluation_id: %). Ledger is immutable.', OLD.evaluation_id
                USING ERRCODE = '23514';
        END IF;

        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS enforce_score_breakdown_immutability ON score_breakdown;

    CREATE TRIGGER enforce_score_breakdown_immutability
    BEFORE UPDATE OR DELETE ON score_breakdown
    FOR EACH ROW
    EXECUTE FUNCTION check_score_breakdown_immutability();
    """
    op.execute(trigger_sql)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS enforce_score_breakdown_immutability ON score_breakdown;")
    op.execute("DROP FUNCTION IF EXISTS check_score_breakdown_immutability();")

    op.drop_table('sync_logs')
    op.drop_table('score_breakdown')
    op.drop_table('pr_comments')
    op.drop_table('pr_reviewers')
    op.drop_table('pull_requests')
    op.drop_table('commit_files')
    op.drop_table('commits')
    op.drop_table('github_connections')
    op.drop_table('evaluations')
    
    evaluation_status_enum = postgresql.ENUM('pending', 'active', 'completed', 'locked', name='evaluation_status_enum')
    evaluation_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_table('role_profiles')
    op.drop_table('recruiters')
