"""Agent 2 of the multi-agent pipeline: terminology and domain detection.

Outputs a natural-language hint that is later concatenated into the translator
agent's system prompt. The hint is what makes a domain-aware translation possible
without requiring the translator to know about every domain in advance.
"""

from .base import AgentResult


_DOMAINS: dict[str, list[str]] = {
    "medical":   ["diagnosis", "syndrome", "therapy", "dosage", "chronic", "acute",
                  "diagnostico", "sindrome", "terapia", "dosis", "cronico", "agudo"],
    "legal":     ["hereby", "pursuant", "jurisdiction", "liability", "clause",
                  "jurisdiccion", "responsabilidad", "clausula", "contrato"],
    "technical": ["algorithm", "bandwidth", "API", "latency", "protocol", "deploy",
                  "algoritmo", "protocolo", "despliegue", "microservicio"],
    "financial": ["dividend", "equity", "leverage", "portfolio", "hedge", "amortize",
                  "dividendo", "patrimonio", "cartera", "apalancamiento"],
    "scientific": ["hypothesis", "methodology", "correlation", "coefficient",
                   "hipotesis", "metodologia", "correlacion", "coeficiente"],
}


class TerminologyAgent:
    name = "terminologo"
    icon = "book"
    description = "Identifica dominio y terminos clave"

    def run(self, text: str) -> AgentResult:
        text_lower = text.lower()
        found: dict[str, list[str]] = {}
        for domain, terms in _DOMAINS.items():
            hits = [t for t in terms if t in text_lower]
            if hits:
                found[domain] = hits

        if not found:
            return AgentResult(
                agent=self.name,
                output="General text. Use natural, fluent language appropriate to the context.",
                metadata={"domain": "general", "terms": {}},
            )

        primary = max(found, key=lambda d: len(found[d]))
        terms_str = ", ".join(found[primary][:5])
        instruction = (
            f"This is {primary} domain text. "
            f"Key terms detected: {terms_str}. "
            f"Preserve technical terminology precisely. "
            f"Use domain-appropriate register."
        )
        return AgentResult(
            agent=self.name,
            output=instruction,
            metadata={"domain": primary, "terms": found},
        )
