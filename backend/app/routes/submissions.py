"""
Submissions Routes
Handles opportunity submission, listing, retrieval, file download, and verdict.
"""

import os
import uuid
import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Submission, SubmissionStatus
from app.schemas import SubmissionResponse, SubmissionListResponse, VerdictRequest, MessageResponse
from app.routes.auth import verify_token, require_evaluator, require_proponent
from app.config import settings
from app.services import document_parser, ai_analyzer, email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


def _validate_file(file: UploadFile):
    """Validate uploaded file type."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do arquivo não informado",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido: {ext}. Aceitos: {', '.join(settings.allowed_extensions)}",
        )


async def _save_file(file: UploadFile) -> tuple[str, str]:
    """Save uploaded file with a secure UUID filename."""
    ext = os.path.splitext(file.filename)[1].lower()
    safe_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    content = await file.read()

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito grande. Máximo: {settings.max_file_size_mb}MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, file.filename


def _process_submission_sync(submission_id: str, file_path: str):
    """
    Background task: extract text, run AI analysis, update DB, send email.
    Runs synchronously in a thread (FastAPI BackgroundTasks).
    """
    import asyncio

    db = SessionLocal()

    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found for processing")
            return

        # Mark as analyzing
        submission.status = SubmissionStatus.ANALYZING
        submission.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Step 1: Extract text from document
        logger.info(f"Extracting text from: {file_path}")
        document_text = document_parser.extract_text(file_path)

        if not document_text or len(document_text.strip()) < 50:
            raise ValueError(
                "O documento não contém texto suficiente para análise. "
                "Verifique se o PDF não é apenas imagens ou se o arquivo está corrompido."
            )

        # Step 2: Run AI analysis
        logger.info(f"Running AI analysis for submission: {submission_id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ai_analyzer.analyze_document(document_text))
        finally:
            loop.close()

        # Step 3: Update submission with results
        submission.ai_analysis = result["analysis"]
        submission.score = result["score"]
        submission.verdict = result["verdict"]
        submission.status = SubmissionStatus.ANALYZED
        submission.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Step 4: Send email to evaluator
        logger.info(f"Sending evaluator notification for: {submission_id}")
        try:
            email_service.send_evaluator_notification(
                submission_id=submission.id,
                proponent_name=submission.full_name,
                proponent_email=submission.email,
                original_filename=submission.original_filename,
                ai_analysis=result["analysis"],
                score=result["score"],
                verdict=result["verdict"],
            )
        except Exception as e:
            logger.error(f"Failed to send evaluator email: {e}")

        logger.info(f"Processing complete for submission: {submission_id}")

    except Exception as e:
        logger.error(f"Error processing submission {submission_id}: {e}")
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                # On error, auto-reject with feedback
                submission.status = SubmissionStatus.REJECTED
                submission.score = 0
                submission.verdict = "ERRO"
                submission.ai_analysis = (
                    f"⚠️ SUBMISSÃO REPROVADA AUTOMATICAMENTE\n\n"
                    f"Não foi possível processar sua submissão. Motivo:\n\n"
                    f"→ {str(e)}\n\n"
                    f"Possíveis causas:\n"
                    f"- O documento enviado pode estar corrompido ou vazio\n"
                    f"- O formato do arquivo pode não ser suportado corretamente\n"
                    f"- O documento pode conter apenas imagens sem texto extraível\n"
                    f"- Quota da API de IA temporariamente esgotada\n\n"
                    f"Recomendação: verifique se o arquivo está legível e tente submeter novamente."
                )
                submission.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_submission(
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Submit a new business opportunity.
    Public endpoint — includes password for proponent future access.
    """
    _validate_file(file)

    if len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter pelo menos 4 caracteres.",
        )

    file_path, original_filename = await _save_file(file)

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    db = SessionLocal()
    try:
        submission = Submission(
            full_name=full_name,
            email=email.strip().lower(),
            phone=phone,
            password_hash=password_hash,
            file_path=file_path,
            original_filename=original_filename,
            status=SubmissionStatus.PENDING_ANALYSIS,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        submission_id = submission.id
    finally:
        db.close()

    # Process in background thread
    background_tasks.add_task(_process_submission_sync, submission_id, file_path)

    return MessageResponse(
        message="Submissão recebida com sucesso! Sua ideia será analisada em breve. Use seu email e senha para acompanhar o andamento.",
        submission_id=submission_id,
    )


# ============================================================
# Evaluator Routes (protected)
# ============================================================

@router.get("/", response_model=list[SubmissionListResponse])
async def list_submissions(
    status_filter: str | None = None,
    _: dict = Depends(require_evaluator),
    db: Session = Depends(get_db),
):
    """List all submissions. Protected — evaluator only."""
    query = db.query(Submission).order_by(Submission.created_at.desc())

    if status_filter:
        try:
            status_enum = SubmissionStatus(status_filter)
            query = query.filter(Submission.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status inválido: {status_filter}",
            )

    return query.all()


@router.get("/my", response_model=list[SubmissionListResponse])
async def list_my_submissions(
    payload: dict = Depends(require_proponent),
    db: Session = Depends(get_db),
):
    """List submissions for the authenticated proponent."""
    email = payload.get("sub", "")
    submissions = (
        db.query(Submission)
        .filter(Submission.email == email)
        .order_by(Submission.created_at.desc())
        .all()
    )
    return submissions


@router.get("/my/{submission_id}", response_model=SubmissionResponse)
async def get_my_submission(
    submission_id: str,
    payload: dict = Depends(require_proponent),
    db: Session = Depends(get_db),
):
    """Get a specific submission for the authenticated proponent."""
    email = payload.get("sub", "")
    submission = (
        db.query(Submission)
        .filter(Submission.id == submission_id, Submission.email == email)
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada",
        )

    return submission


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    _: dict = Depends(require_evaluator),
    db: Session = Depends(get_db),
):
    """Get a specific submission. Protected — evaluator only."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada",
        )

    return submission


@router.get("/{submission_id}/file")
async def download_submission_file(
    submission_id: str,
    _: dict = Depends(require_evaluator),
    db: Session = Depends(get_db),
):
    """Download the submitted file. Protected — evaluator only."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada",
        )

    if not os.path.exists(submission.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado no servidor",
        )

    # Format: Nome_do_Proponente_YYYY-MM-DD_original_filename.ext
    safe_name = submission.full_name.replace(" ", "_")
    date_str = submission.created_at.strftime("%Y-%m-%d")
    download_filename = f"{safe_name}_{date_str}_{submission.original_filename}"

    return FileResponse(
        path=submission.file_path,
        filename=download_filename,
        media_type="application/octet-stream",
    )


@router.patch("/{submission_id}/verdict", response_model=MessageResponse)
async def set_verdict(
    submission_id: str,
    verdict_request: VerdictRequest,
    _: dict = Depends(require_evaluator),
    db: Session = Depends(get_db),
):
    """Approve or reject a submission. Protected — evaluator only."""
    if verdict_request.action not in ("approve", "reject"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ação inválida. Use 'approve' ou 'reject'.",
        )

    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada",
        )

    if submission.status not in (SubmissionStatus.ANALYZED, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submissão não pode ser avaliada no estado atual: {submission.status.value}",
        )

    is_approved = verdict_request.action == "approve"
    submission.status = SubmissionStatus.APPROVED if is_approved else SubmissionStatus.REJECTED
    submission.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Send result email to proponent
    try:
        email_service.send_proponent_result(
            to_email=submission.email,
            proponent_name=submission.full_name,
            is_approved=is_approved,
            original_filename=submission.original_filename,
        )
        email_status = "Email enviado ao proponente."
    except Exception as e:
        logger.error(f"Failed to send proponent email: {e}")
        email_status = "Aviso: Falha ao enviar email ao proponente."

    action_text = "aprovada" if is_approved else "reprovada"
    return MessageResponse(
        message=f"Oportunidade {action_text} com sucesso. {email_status}",
        submission_id=submission_id,
    )
