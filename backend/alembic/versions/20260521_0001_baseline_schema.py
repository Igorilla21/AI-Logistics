"""Baseline persistence schema.

Revision ID: 20260521_0001
Revises:
Create Date: 2026-05-21 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260521_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_packs",
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("pack_id"),
    )
    op.create_index("ix_document_packs_created_at", "document_packs", ["created_at"], unique=False)

    op.create_table(
        "validation_reports",
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("report_id"),
    )
    op.create_index("ix_validation_reports_generated_at", "validation_reports", ["generated_at"], unique=False)
    op.create_index("ix_validation_reports_pack_id", "validation_reports", ["pack_id"], unique=False)

    op.create_table(
        "document_files",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["pack_id"], ["document_packs.pack_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index("ix_document_files_pack_id", "document_files", ["pack_id"], unique=False)
    op.create_index("ix_document_files_uploaded_at", "document_files", ["uploaded_at"], unique=False)

    op.create_table(
        "normalized_documents",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=128), nullable=False),
        sa.Column("source_file_name", sa.String(length=512), nullable=False),
        sa.Column("extraction_status", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["pack_id"], ["document_packs.pack_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index("ix_normalized_documents_document_type", "normalized_documents", ["document_type"], unique=False)
    op.create_index("ix_normalized_documents_pack_id", "normalized_documents", ["pack_id"], unique=False)

    op.create_table(
        "ocr_document_results",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_file_name", sa.String(length=512), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["pack_id"], ["document_packs.pack_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id"),
    )
    op.create_index("ix_ocr_document_results_created_at", "ocr_document_results", ["created_at"], unique=False)
    op.create_index("ix_ocr_document_results_pack_id", "ocr_document_results", ["pack_id"], unique=False)

    op.create_table(
        "validation_results",
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("pack_id", sa.String(length=36), nullable=False),
        sa.Column("rule_code", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["validation_reports.report_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id", "rule_code"),
    )
    op.create_index("ix_validation_results_created_at", "validation_results", ["created_at"], unique=False)
    op.create_index("ix_validation_results_pack_id", "validation_results", ["pack_id"], unique=False)
    op.create_index("ix_validation_results_report_id", "validation_results", ["report_id"], unique=False)
    op.create_index("ix_validation_results_rule_code", "validation_results", ["rule_code"], unique=False)
    op.create_index("ix_validation_results_severity", "validation_results", ["severity"], unique=False)
    op.create_index("ix_validation_results_status", "validation_results", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_validation_results_status", table_name="validation_results")
    op.drop_index("ix_validation_results_severity", table_name="validation_results")
    op.drop_index("ix_validation_results_rule_code", table_name="validation_results")
    op.drop_index("ix_validation_results_report_id", table_name="validation_results")
    op.drop_index("ix_validation_results_pack_id", table_name="validation_results")
    op.drop_index("ix_validation_results_created_at", table_name="validation_results")
    op.drop_table("validation_results")

    op.drop_index("ix_ocr_document_results_pack_id", table_name="ocr_document_results")
    op.drop_index("ix_ocr_document_results_created_at", table_name="ocr_document_results")
    op.drop_table("ocr_document_results")

    op.drop_index("ix_normalized_documents_pack_id", table_name="normalized_documents")
    op.drop_index("ix_normalized_documents_document_type", table_name="normalized_documents")
    op.drop_table("normalized_documents")

    op.drop_index("ix_document_files_uploaded_at", table_name="document_files")
    op.drop_index("ix_document_files_pack_id", table_name="document_files")
    op.drop_table("document_files")

    op.drop_index("ix_validation_reports_pack_id", table_name="validation_reports")
    op.drop_index("ix_validation_reports_generated_at", table_name="validation_reports")
    op.drop_table("validation_reports")

    op.drop_index("ix_document_packs_created_at", table_name="document_packs")
    op.drop_table("document_packs")
