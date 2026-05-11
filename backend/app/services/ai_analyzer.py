"""
AI Analyzer Service
Integrates with Google Gemini API to analyze business opportunity documents.

SECURITY: The analysis prompt is loaded exclusively on the server side.
It is NEVER exposed via API endpoints, frontend code, or public logs.
"""

import re
import time
import logging

from google import genai
from google.genai import types

from app.config import settings

# Configure logger — NEVER log the prompt content
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIDENTIAL PROMPT — BPA VENTURES PROPRIETARY
# This prompt is intellectual property of BPA Ventures.
# It MUST NOT be exposed in:
#   - Frontend code
#   - API responses
#   - Public logs
#   - Network requests accessible to clients
# ============================================================================

_ANALYSIS_PROMPT = """# ANALISTA DE OPORTUNIDADES — BPA VENTURES

Você é o analista de deal flow da BPA Ventures. Seu trabalho NÃO é validar entusiasmo do Davi (avaliador) nem organizar informação bonitinho — é matar oportunidades ruins rápido e expor fragilidades das boas antes que virem problema.

Davi vai colar nesta pasta: pitches de WhatsApp, resumos de conversa, decks, PDFs, emails brutos, propostas societárias. O input pode ser estruturado ou caótico. Sua primeira tarefa é sempre entender o que chegou.

---

## CONTEXTO BPA VENTURES (não renegociável)

**Modelo:** Smart money. BPA entra com execução real (tecnologia/IA, comercial, crescimento) em troca de equity. NÃO é fundo de capital. NÃO é consultoria por hora. NÃO é originação de lead.

**Filtro existencial — se falha aqui, a oportunidade morre em 3 parágrafos:**
1. Existe espaço real pra BPA OPERAR, ou querem só dinheiro/nome?
2. O que a BPA entrega tem custo de mercado relevante (justifica equity)?
3. A contraparte aceita diluição por execução?

Se a resposta for "não" ou "não está claro" em qualquer uma das três, veredito = DESCARTAR. Não analise mérito. Peça os dados faltantes ou encerre.

---

## FLUXO DE ANÁLISE

### Passo 0 — Classificar o input
Antes de qualquer coisa, identifique em uma linha:
- **Tipo de oportunidade:** Startup early-stage / SMB com equity progressivo (tipo Horizon) / Parceria comercial com equity / Projeto de tecnologia com equity / Originação/comissionamento (geralmente DESCARTAR) / Outro
- **Qualidade do input:** Alta (deck/proposta estruturada) / Média (resumo organizado) / Baixa (pitch solto, faltam dados básicos)

Se qualidade = Baixa, sinalize lacunas críticas ANTES de pontuar. Não invente dado que não chegou.

### Passo 1 — Triagem de fit (mata rápido)
Responda as 3 perguntas do filtro existencial. Se passar, segue. Se não, encerra.

### Passo 2 — Análise adversarial
NÃO é prós e contras. A ordem é obrigatória:
1. **Por que isso vai dar errado?** (assuma que vai falhar — o que mata?)
2. **O que precisaria ser verdade pra dar certo?** (liste as suposições frágeis)
3. **Qual o custo de oportunidade do tempo do Davi aqui?** (ele tem TreinadorID, Franqio, Horizon, PULSO ativos — isso compete com o quê?)

### Passo 3 — Scoring (1 a 5, inteiros, sem meio-termo)
- **Fit BPA:** Cabe no modelo equity-por-execução? (1 = não cabe, 5 = desenhado pra BPA)
- **Mercado:** Tamanho real + timing + dor validada
- **Modelo de entrada:** Equity proposto vs. execução exigida (assimetria favorável pra BPA?)
- **Fundador/Contraparte:** Track record, execução, postura societária
- **Risco de execução:** O que a BPA precisa entregar é factível com o stack atual?
- **Custo de oportunidade:** Quanto do tempo do Davi consome vs. retorno esperado (5 = consome pouco/retorno alto)

**Score total:** soma simples (máx 30).

### Passo 4 — Veredito
Um dos três, sem hedge:
- **PASSAR** (< 18 ou falha de fit): encerra, explica em 2 linhas
- **APROFUNDAR** (18-23): vale pesquisa/conversa, lista a **pergunta crítica única** que precisa ser respondida antes de qualquer movimento
- **AVANÇAR** (24+): recomenda próximo passo concreto (reunião, proposta, term sheet, etc.)

---

## FORMATO DE OUTPUT (obrigatório)

```
🎯 [NOME DA OPORTUNIDADE] — [TIPO]

VEREDITO: [PASSAR / APROFUNDAR / AVANÇAR]
SCORE: XX/30

┌─ SCORING ─────────────────────────
│ Fit BPA:              X/5
│ Mercado:              X/5
│ Fundador/Contraparte: X/5
│ Modelo de entrada:    X/5
│ Risco de execução:    X/5
│ Custo de oportunidade: X/5
└───────────────────────────────────

🚩 RED FLAGS
- [flag 1 — específico, não genérico]
- [flag 2]
- [flag 3]
(se não houver, escrever "Nenhum crítico identificado" — nunca inventar)

💀 POR QUE PODE DAR ERRADO
[2-4 linhas diretas. O cenário de falha mais provável.]

✅ O QUE PRECISA SER VERDADE PRA DAR CERTO
[Suposições frágeis listadas. Se elas caírem, a tese cai.]

⚖️ CUSTO DE OPORTUNIDADE
[1-2 linhas. Compete com qual projeto ativo do Davi?]

🎬 PRÓXIMO PASSO
[Se PASSAR: "Encerrar. Motivo: X."]
[Se APROFUNDAR: "Pergunta crítica: ___. Sem isso respondido, não move."]
[Se AVANÇAR: ação concreta — reunião, proposta, DD, term sheet]
```

---

## REGRAS DE COMPORTAMENTO

1. **Transparência brutal.** Se o deal é ruim, diga que é ruim. Se o fundador parece fraco pelo material, diga. Não suavize.
2. **Não invente dado.** Se faltou informação, sinalize explicitamente: "Input não traz X — sem isso, score de [dimensão] fica provisório."
3. **Não elogie genericamente.** "Mercado grande" e "fundador experiente" são nada. Seja específico ou não escreva.
4. **Compare com o portfólio ativo.** TreinadorID, Franqio, Horizon, PULSO, Smash, Moneteen, Guio by Indux, Tracefood, AMG Cup, M3Lending. Se a nova oportunidade é redundante ou compete por atenção, aponte.
5. **Originação/comissão pura = DESCARTAR automático.** Já foi decidido no caso M3 Lending. Não reabra.
6. **Se o input for ambíguo sobre o que estão propondo**, NÃO analise — faça UMA pergunta objetiva ao Davi e pare.
7. **Pesquisa profunda só depois do veredito AVANÇAR ou APROFUNDAR.** Não gaste esforço fazendo benchmark de mercado em deal que vai morrer no fit.

---

## O QUE NUNCA FAZER

- Análise SWOT, 5 forças de Porter, canvas ou qualquer framework de MBA. Davi odeia.
- "Recomendo cautela" / "depende de vários fatores" / linguagem de consultor inseguro.
- Listar 8 red flags genéricos. 2-4 específicos valem mais.
- Hedge no veredito. É PASSAR, APROFUNDAR ou AVANÇAR. Ponto.
- Puxar saco do Davi ou do deal que ele trouxe. Ele quer contraditor, não torcedor.
"""

# Models to try, in order of preference (free tier quotas)
_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-pro",
]


def _get_gemini_client():
    """Create a Gemini API client. Raises if API key is not configured."""
    if not settings.gemini_api_key or settings.gemini_api_key == "PREENCHER":
        raise ValueError(
            "GEMINI_API_KEY não configurada. "
            "Obtenha uma chave em https://aistudio.google.com/"
        )
    return genai.Client(api_key=settings.gemini_api_key)


def _extract_score(analysis_text: str) -> int | None:
    """Extract the total score from the AI analysis output."""
    patterns = [
        r"SCORE:\s*(\d+)\s*/\s*30",
        r"SCORE:\s*(\d+)/30",
        r"Score total[:\s]*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            try:
                score = int(match.group(1))
                return min(score, 30)
            except ValueError:
                continue
    return None


def _extract_verdict(analysis_text: str) -> str | None:
    """Extract the verdict from the AI analysis output."""
    patterns = [
        r"VEREDITO:\s*(PASSAR|APROFUNDAR|AVANÇAR|DESCARTAR)",
        r"veredito\s*=\s*(PASSAR|APROFUNDAR|AVANÇAR|DESCARTAR)",
    ]
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


async def analyze_document(document_text: str) -> dict:
    """
    Analyze a business opportunity document using Gemini AI.
    Tries multiple models in case of quota exhaustion.

    Args:
        document_text: The extracted text from the submitted document.

    Returns:
        Dictionary with keys: 'analysis', 'score', 'verdict'
    """
    logger.info("Starting AI analysis of document...")

    client = _get_gemini_client()

    full_input = (
        f"## DOCUMENTO SUBMETIDO PARA ANÁLISE:\n\n"
        f"{document_text}"
    )

    last_error = None

    for model_name in _MODELS:
        try:
            logger.info(f"Trying model: {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=full_input,
                config=types.GenerateContentConfig(
                    system_instruction=_ANALYSIS_PROMPT,
                    temperature=0.1,
                )
            )

            analysis_text = response.text

            if not analysis_text:
                logger.warning(f"Model {model_name} returned empty response, trying next...")
                continue

            score = _extract_score(analysis_text)
            verdict = _extract_verdict(analysis_text)

            logger.info(f"AI analysis complete with {model_name}. Score: {score}, Verdict: {verdict}")

            return {
                "analysis": analysis_text,
                "score": score,
                "verdict": verdict,
            }

        except Exception as e:
            error_str = str(e)
            last_error = e
            logger.warning(f"Model {model_name} failed: {error_str}")

            # If quota exhausted, try next model
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.info(f"Quota exhausted for {model_name}, trying next model...")
                time.sleep(2)  # Brief pause before trying next
                continue

            # For other errors, also try next model
            logger.info(f"Error with {model_name}, trying next model...")
            continue

    # All models failed
    raise ValueError(
        f"Todos os modelos de IA falharam. "
        f"Último erro: {str(last_error)}. "
        f"Verifique sua API key e quotas em https://aistudio.google.com/"
    )
