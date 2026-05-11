"""
Email Service
Handles sending automated emails to evaluators and proponents.
Uses Gmail SMTP with App Password for authentication.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


def _create_smtp_connection():
    """Create and authenticate an SMTP connection to Gmail."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.smtp_email, settings.smtp_password)
        return server
    except Exception as e:
        logger.error(f"Failed to connect to SMTP: {type(e).__name__}: {e}")
        raise


def _send_email(to_email: str, subject: str, html_body: str):
    """Send an email with HTML body."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"BPA Ventures <{settings.smtp_email}>"
        msg["To"] = to_email

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        server = _create_smtp_connection()
        server.sendmail(settings.smtp_email, to_email, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


def send_evaluator_notification(
    submission_id: str,
    proponent_name: str,
    proponent_email: str,
    original_filename: str,
    ai_analysis: str,
    score: int | None,
    verdict: str | None,
):
    """
    Send notification email to the evaluator with AI analysis results
    and a link to the evaluation platform.
    """
    evaluation_link = f"{settings.frontend_url}/avaliacao/{submission_id}"

    # Format the analysis for email (replace newlines with <br>)
    formatted_analysis = ai_analysis.replace("\n", "<br>")

    score_display = f"{score}/30" if score else "N/A"
    verdict_display = verdict or "N/A"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0a0e1a;
                color: #e0e6ed;
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                background: linear-gradient(135deg, #111827 0%, #1a1f35 100%);
                border-radius: 16px;
                padding: 40px;
                border: 1px solid rgba(99, 179, 237, 0.15);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #63b3ed;
                font-size: 24px;
                margin: 0;
            }}
            .header p {{
                color: #8892a4;
                font-size: 14px;
                margin-top: 8px;
            }}
            .info-card {{
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid rgba(255,255,255,0.08);
            }}
            .info-card h3 {{
                color: #63b3ed;
                margin-top: 0;
                font-size: 16px;
            }}
            .info-card p {{
                margin: 6px 0;
                color: #c0c8d4;
                font-size: 14px;
            }}
            .score-badge {{
                display: inline-block;
                background: linear-gradient(135deg, #2563eb, #7c3aed);
                color: white;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 18px;
                margin-right: 12px;
            }}
            .verdict-badge {{
                display: inline-block;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
                text-transform: uppercase;
            }}
            .analysis-box {{
                background: rgba(0,0,0,0.3);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.6;
                color: #d0d8e4;
                border: 1px solid rgba(255,255,255,0.06);
                max-height: 500px;
                overflow-y: auto;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #2563eb, #7c3aed);
                color: white !important;
                text-decoration: none;
                padding: 14px 36px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
                margin-top: 20px;
            }}
            .center {{
                text-align: center;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #5a6478;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Nova Oportunidade Recebida</h1>
                <p>Uma nova ideia de negócio foi submetida e analisada pela IA</p>
            </div>

            <div class="info-card">
                <h3>📋 Dados do Proponente</h3>
                <p><strong>Nome:</strong> {proponent_name}</p>
                <p><strong>Email:</strong> {proponent_email}</p>
                <p><strong>Documento:</strong> {original_filename}</p>
            </div>

            <div class="info-card">
                <h3>🤖 Resultado da Análise IA</h3>
                <p>
                    <span class="score-badge">Score: {score_display}</span>
                    <span class="verdict-badge">{verdict_display}</span>
                </p>
            </div>

            <div class="analysis-box">
                {formatted_analysis}
            </div>

            <div class="center">
                <a href="{evaluation_link}" class="cta-button">
                    Acessar Plataforma de Avaliação →
                </a>
            </div>

            <div class="footer">
                <p>BPA Ventures — Plataforma de Avaliação de Oportunidades</p>
                <p>Este email foi enviado automaticamente. Não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[BPA Ventures] Nova Oportunidade: {proponent_name} — {verdict_display}"

    _send_email(settings.evaluator_email, subject, html_body)


def send_proponent_result(
    to_email: str,
    proponent_name: str,
    is_approved: bool,
    original_filename: str,
):
    """
    Send the evaluation result to the proponent.
    """
    status_text = "APROVADA ✅" if is_approved else "REPROVADA ❌"
    status_color = "#22c55e" if is_approved else "#ef4444"

    if is_approved:
        message_body = """
        <p>Temos o prazer de informar que sua proposta foi <strong>aprovada</strong> pela nossa equipe de avaliação.</p>
        <p>Em breve entraremos em contato para discutir os próximos passos e avançar com a parceria.</p>
        <p>Agradecemos por compartilhar sua ideia conosco!</p>
        """
    else:
        message_body = """
        <p>Após análise cuidadosa, informamos que sua proposta <strong>não foi aprovada</strong> neste momento.</p>
        <p>Isso não significa que sua ideia não tenha mérito — apenas que, no momento, ela não se encaixa no modelo de atuação da BPA Ventures.</p>
        <p>Encorajamos você a continuar desenvolvendo sua ideia e, caso haja evoluções significativas, fique à vontade para submeter novamente no futuro.</p>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0a0e1a;
                color: #e0e6ed;
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: linear-gradient(135deg, #111827 0%, #1a1f35 100%);
                border-radius: 16px;
                padding: 40px;
                border: 1px solid rgba(99, 179, 237, 0.15);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #63b3ed;
                font-size: 22px;
                margin: 0;
            }}
            .status-badge {{
                display: block;
                text-align: center;
                background: rgba(255,255,255,0.05);
                border: 2px solid {status_color};
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }}
            .status-badge h2 {{
                color: {status_color};
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                color: #c0c8d4;
                line-height: 1.7;
                font-size: 15px;
            }}
            .doc-info {{
                background: rgba(255,255,255,0.04);
                border-radius: 8px;
                padding: 12px 16px;
                margin: 16px 0;
                font-size: 13px;
                color: #8892a4;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #5a6478;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>BPA Ventures — Resultado da Avaliação</h1>
            </div>

            <p style="color: #c0c8d4;">Olá, <strong>{proponent_name}</strong>!</p>

            <div class="status-badge">
                <h2>{status_text}</h2>
            </div>

            <div class="doc-info">
                📄 Documento avaliado: <strong>{original_filename}</strong>
            </div>

            <div class="content">
                {message_body}
            </div>

            <div class="footer">
                <p>BPA Ventures — Plataforma de Avaliação de Oportunidades</p>
                <p>Este email foi enviado automaticamente. Não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = f"[BPA Ventures] Resultado da sua submissão: {status_text.split()[0]}"

    _send_email(to_email, subject, html_body)
