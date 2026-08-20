import logging
import re
from collections import Counter

from app.domain.models import ResumeData

logger = logging.getLogger(__name__)


class FraudDetector:
    def analyze(self, resume: ResumeData) -> dict:
        raw_text = resume.raw_text or ""
        text_lower = raw_text.lower()

        result = {
            "keyword_stuffing_indicators": [],
            "ai_generation_indicators": [],
            "template_indicators": [],
            "repeated_phrases": [],
            "signals": [],
        }

        if not raw_text:
            return result

        self._check_keyword_stuffing(text_lower, result)
        self._check_ai_generation(text_lower, result)
        self._check_templates(raw_text, result)
        self._check_repeated_phrases(text_lower, result)
        self._check_placeholder_patterns(raw_text, result)

        return result

    def _check_keyword_stuffing(self, text_lower: str, result: dict) -> None:
        buzzwords = [
            "team player", "hardworking", "motivated", "results-driven",
            "detail-oriented", "excellent communication", "proven track record",
            "think outside the box", "synergy", "self-starter", "go-getter",
            "strategic thinker", "cutting edge", "world class",
        ]
        excessive = [(w, text_lower.count(w)) for w in buzzwords if text_lower.count(w) > 3]
        if excessive:
            for word, count in excessive:
                result["keyword_stuffing_indicators"].append(f"'{word}' appears {count} times")
            result["signals"].append("keyword_stuffing")

    def _check_ai_generation(self, text_lower: str, result: dict) -> None:
        ai_markers = [
            "as an ai", "i don't have personal", "i cannot", "i am an ai",
            "as a language model", "i don't have access to", "i cannot provide",
        ]
        found = [m for m in ai_markers if m in text_lower]
        if found:
            result["ai_generation_indicators"] = found
            result["signals"].append("ai_generated_content")

        trans_phrases = ["in addition", "furthermore", "moreover", "additionally", "consequently", "nevertheless", "in conclusion", "it is important to note", "it is worth noting"]
        trans_count = sum(text_lower.count(p) for p in trans_phrases)
        sentences = [s for s in re.split(r"[.!?]+", text_lower) if len(s.strip().split()) >= 3]
        if sentences and trans_count / len(sentences) > 0.25:
            result["ai_generation_indicators"].append(f"high transitional phrase density ({trans_count}/{len(sentences)})")
            if "ai_generated_content" not in result["signals"]:
                result["signals"].append("ai_generated_content")

    def _check_templates(self, text: str, result: dict) -> None:
        markers = ["[insert", "[your name]", "[company name]", "[job title]", "lorem ipsum"]
        found = [m for m in markers if m.lower() in text.lower()]
        if found:
            result["template_indicators"] = found
            result["signals"].append("template_abuse")

    def _check_repeated_phrases(self, text_lower: str, result: dict) -> None:
        sentences = [s.strip() for s in re.split(r"[.!?]+", text_lower) if len(s.strip().split()) > 3]
        seen = Counter(sentences)
        repeated = [s for s, c in seen.most_common(5) if c > 2]
        if repeated:
            result["repeated_phrases"] = repeated
            result["signals"].append("repeated_phrases")

    def _check_placeholder_patterns(self, text: str, result: dict) -> None:
        patterns = [r"\[\s*insert\s*.*?\]", r"\[\s*your\s+name\s*\]", r"xxxx+", r"click\s+here", r"replace\s+with"]
        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)
        if found:
            result["template_indicators"].extend(found[:3])
            if "template_abuse" not in result["signals"]:
                result["signals"].append("template_abuse")
