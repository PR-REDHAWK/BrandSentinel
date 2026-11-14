import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import Organization, User, UserRole
from app.models.audit import (
    AuditEngine,
    ContentVersion,
    DecisionAction,
    Finding,
    FindingDecision,
    FindingSeverity,
    Submission,
    SubmissionStatus,
)
from app.models.log import AuditLog
from app.routers.governance import (
    CommentCreate,
    DecisionCreate,
    EscalatePayload,
    SignOffPayload,
    add_review_comment,
    escalate_submission,
    export_approved_content,
    list_review_comments,
    record_finding_decision,
    sign_off_submission,
    submit_for_review,
)
from app.routers.analytics import get_governance_analytics
from app.routers.admin import (
    UpdateRoleRequest,
    UpdateStatusRequest,
    get_organization_profile,
    list_audit_trail,
    list_organization_users,
    update_user_role,
    update_user_status,
)


@pytest.fixture
def gov_test_setup(db: Session):
    org = Organization(name="GovCorp", slug="govcorp")
    db.add(org)
    db.flush()

    admin_user = User(
        organization_id=org.id,
        email="admin@govcorp.com",
        hashed_password="pw",
        full_name="Alice Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    reviewer_user = User(
        organization_id=org.id,
        email="reviewer@govcorp.com",
        hashed_password="pw",
        full_name="Bob Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    creator_user = User(
        organization_id=org.id,
        email="creator@govcorp.com",
        hashed_password="pw",
        full_name="Charlie Creator",
        role=UserRole.CREATOR,
        is_active=True,
    )
    db.add_all([admin_user, reviewer_user, creator_user])
    db.flush()

    submission = Submission(
        organization_id=org.id,
        creator_id=creator_user.id,
        title="Q1 Product Launch Press Release",
        target_channel="PR & Social",
        current_status=SubmissionStatus.DRAFT,
    )
    db.add(submission)
    db.flush()

    version = ContentVersion(
        submission_id=submission.id,
        version_number=1,
        raw_content="Our platform is dirt cheap and guarantees 100% cloud cost reduction.",
        audit_score=68.5,
    )
    db.add(version)
    db.flush()

    # High severity finding (Claim mismatch)
    finding_high = Finding(
        content_version_id=version.id,
        rule_id="RULE-FACT-001",
        category="FACT_CHECK",
        severity=FindingSeverity.HIGH,
        title="Unverified Cloud Cost Claim",
        detected_content="guarantees 100% cloud cost reduction",
        explanation="Approved benchmark states savings up to 30%, not 100%.",
        source_citation="Audited Cloud Benchmark 2025, p. 4",
        suggested_correction="helps reduce infrastructure costs by up to 30%",
        confidence_score=0.98,
        engine=AuditEngine.RAG_LLM,
        requires_human_review=True,
    )

    # Medium severity finding (Banned term)
    finding_med = Finding(
        content_version_id=version.id,
        rule_id="RULE-TERM-002",
        category="BANNED_TERM",
        severity=FindingSeverity.MEDIUM,
        title="Banned Term Detected",
        detected_content="dirt cheap",
        explanation="Informal slang.",
        source_citation="Brand Guidelines v2.1, Section 3.1",
        suggested_correction="cost-effective",
        confidence_score=1.0,
        engine=AuditEngine.DETERMINISTIC,
        requires_human_review=False,
    )
    db.add_all([finding_high, finding_med])
    db.commit()

    return {
        "org": org,
        "admin": admin_user,
        "reviewer": reviewer_user,
        "creator": creator_user,
        "submission": submission,
        "version": version,
        "finding_high": finding_high,
        "finding_med": finding_med,
    }


def test_finding_decisions_and_validation(db: Session, gov_test_setup: dict):
    creator = gov_test_setup["creator"]
    finding_high = gov_test_setup["finding_high"]
    finding_med = gov_test_setup["finding_med"]

    # 1. Accept medium finding
    dec1 = record_finding_decision(
        finding_id=finding_med.id,
        payload=DecisionCreate(decision=DecisionAction.ACCEPTED),
        current_user=creator,
        db=db,
    )
    assert dec1.decision == DecisionAction.ACCEPTED
    assert dec1.finding_id == finding_med.id

    # 2. Edit finding with custom text
    dec2 = record_finding_decision(
        finding_id=finding_high.id,
        payload=DecisionCreate(
            decision=DecisionAction.EDITED,
            custom_edit="helps reduce cloud costs by up to 30% according to audited metrics",
        ),
        current_user=creator,
        db=db,
    )
    assert dec2.decision == DecisionAction.EDITED
    assert "audited metrics" in dec2.custom_edit

    # 3. Reject with reason
    dec3 = record_finding_decision(
        finding_id=finding_med.id,
        payload=DecisionCreate(
            decision=DecisionAction.REJECTED,
            rejection_reason="Executive team explicitly authorized this phrase for satirical ad campaign.",
        ),
        current_user=creator,
        db=db,
    )
    assert dec3.decision == DecisionAction.REJECTED
    assert "satirical ad" in dec3.rejection_reason


def test_review_workflow_and_guardrail_blocking(db: Session, gov_test_setup: dict):
    creator = gov_test_setup["creator"]
    reviewer = gov_test_setup["reviewer"]
    submission = gov_test_setup["submission"]
    finding_high = gov_test_setup["finding_high"]

    # 1. Creator submits for review
    sub_res = submit_for_review(submission.id, current_user=creator, db=db)
    assert sub_res.current_status == SubmissionStatus.IN_REVIEW

    # 2. Reviewer attempts sign-off with approved=True, but finding_high has NO decision yet
    with pytest.raises(HTTPException) as exc_info:
        sign_off_submission(
            submission.id,
            payload=SignOffPayload(approved=True, notes="Looks good"),
            current_user=reviewer,
            db=db,
        )
    assert exc_info.value.status_code == 400
    assert "high-severity findings have not been resolved" in exc_info.value.detail

    # 3. Reviewer escalates the submission
    esc_res = escalate_submission(
        submission.id,
        payload=EscalatePayload(reason="Exaggerated 100% claim must be reviewed by Legal counsel."),
        current_user=reviewer,
        db=db,
    )
    assert esc_res.current_status == SubmissionStatus.ESCALATED

    # 4. Creator resolves the high-severity finding by accepting the suggested fix
    record_finding_decision(
        finding_id=finding_high.id,
        payload=DecisionCreate(decision=DecisionAction.ACCEPTED),
        current_user=creator,
        db=db,
    )

    # 5. Now Reviewer sign-off with approved=True succeeds
    approved_res = sign_off_submission(
        submission.id,
        payload=SignOffPayload(approved=True, notes="Approved after claim was corrected to 30%."),
        current_user=reviewer,
        db=db,
    )
    assert approved_res.current_status == SubmissionStatus.APPROVED


def test_version_locked_export_certificate(db: Session, gov_test_setup: dict):
    creator = gov_test_setup["creator"]
    reviewer = gov_test_setup["reviewer"]
    submission = gov_test_setup["submission"]
    finding_high = gov_test_setup["finding_high"]

    # Attempt export while in DRAFT -> must fail with 400
    with pytest.raises(HTTPException) as exc_info:
        export_approved_content(submission.id, current_user=creator, db=db)
    assert exc_info.value.status_code == 400
    assert "Only APPROVED content can be exported" in exc_info.value.detail

    # Resolve finding and approve
    record_finding_decision(
        finding_id=finding_high.id,
        payload=DecisionCreate(decision=DecisionAction.ACCEPTED),
        current_user=creator,
        db=db,
    )
    sign_off_submission(
        submission.id,
        payload=SignOffPayload(approved=True, notes="Verified & Certified"),
        current_user=reviewer,
        db=db,
    )

    # Export approved artifact
    cert = export_approved_content(submission.id, current_user=creator, db=db)
    assert cert["approval_status"] == "VERSION_LOCKED_APPROVED"
    assert cert["organization"] == "GovCorp"
    assert cert["brand_compliance_score"] == 68.5
    assert cert["signee_notes"] == "Verified & Certified"
    assert "No finding without cited evidence" in cert["governance_notice"]
    assert len(cert["audit_summary"]) >= 1


def test_review_comments_thread(db: Session, gov_test_setup: dict):
    creator = gov_test_setup["creator"]
    reviewer = gov_test_setup["reviewer"]
    submission = gov_test_setup["submission"]

    # Reviewer adds comment
    comment = add_review_comment(
        submission.id,
        payload=CommentCreate(comment="Please update the headline to align with the Q1 brand brief."),
        current_user=reviewer,
        db=db,
    )
    assert comment.comment == "Please update the headline to align with the Q1 brand brief."

    # Creator replies
    reply = add_review_comment(
        submission.id,
        payload=CommentCreate(comment="Updated accordingly in the second revision."),
        current_user=creator,
        db=db,
    )

    # List comments
    comments = list_review_comments(submission.id, current_user=creator, db=db)
    assert len(comments) == 2
    assert comments[0].user_id == reviewer.id
    assert comments[1].user_id == creator.id


def test_governance_analytics_dashboard(db: Session, gov_test_setup: dict):
    creator = gov_test_setup["creator"]
    finding_high = gov_test_setup["finding_high"]
    finding_med = gov_test_setup["finding_med"]

    # Record some decisions
    record_finding_decision(
        finding_id=finding_high.id,
        payload=DecisionCreate(decision=DecisionAction.ACCEPTED),
        current_user=creator,
        db=db,
    )
    record_finding_decision(
        finding_id=finding_med.id,
        payload=DecisionCreate(decision=DecisionAction.REJECTED, rejection_reason="Conflicting guideline clause"),
        current_user=creator,
        db=db,
    )

    # Fetch live analytics
    data = get_governance_analytics(current_user=creator, db=db)

    assert data["overview"]["total_submissions"] == 1
    assert data["overview"]["average_compliance_score"] == 68.5
    assert "FACT_CHECK" in data["violations_by_category"] or "BANNED_TERM" in data["violations_by_category"]
    assert data["creator_actions"]["accepted"] == 1
    assert data["creator_actions"]["rejected"] == 1
    assert data["creator_actions"]["acceptance_rate_pct"] == 50.0
    assert len(data["guideline_ambiguity_ranking"]) >= 1
    assert "conflicting" in data["guideline_ambiguity_ranking"][0]["insight"]


def test_admin_user_management_and_audit_trail(db: Session, gov_test_setup: dict):
    admin = gov_test_setup["admin"]
    creator = gov_test_setup["creator"]

    # 1. Organization profile
    org_info = get_organization_profile(current_user=admin, db=db)
    assert org_info["name"] == "GovCorp"
    assert org_info["total_members"] == 3

    # 2. List organization users
    users = list_organization_users(current_user=admin, db=db)
    assert len(users) == 3

    # 3. Promote Creator to Reviewer
    promoted = update_user_role(
        user_id=creator.id,
        payload=UpdateRoleRequest(role=UserRole.REVIEWER),
        current_user=admin,
        db=db,
    )
    assert promoted.role == UserRole.REVIEWER

    # 4. Sole admin protection: demoting Alice Admin should fail
    with pytest.raises(HTTPException) as exc_info:
        update_user_role(
            user_id=admin.id,
            payload=UpdateRoleRequest(role=UserRole.CREATOR),
            current_user=admin,
            db=db,
        )
    assert exc_info.value.status_code == 400
    assert "sole active administrator" in exc_info.value.detail

    # 5. Deactivate user
    deactivated = update_user_status(
        user_id=creator.id,
        payload=UpdateStatusRequest(is_active=False),
        current_user=admin,
        db=db,
    )
    assert deactivated.is_active is False

    # 6. Query audit logs
    logs = list_audit_trail(limit=50, offset=0, event_type=None, current_user=admin, db=db)
    assert len(logs) >= 2
    event_types = [l.event_type for l in logs]
    assert "USER_ROLE_CHANGED" in event_types
    assert "USER_STATUS_CHANGED" in event_types
