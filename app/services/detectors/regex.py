import re
from typing import Dict, Any
from app.services.detectors.base import BaseDetector
from app.core.taxonomy import IntentCategory

class RegexDetector(BaseDetector):
    def __init__(self):
        # Initialize patterns and compiled as empty, they will be loaded asynchronously
        self.patterns = {}
        self.compiled = {}

    async def load(self):
        # Compile regex patterns for different intents
        self.patterns = {
            IntentCategory.PROMPT_INJECTION: [
                # Standard Injection
                r"ignore previous instructions",
                r"ignore all rules",
                r"reveal your system prompt",
                r"system prompt",
                r"forget all instructions",
                r"disregard safety",
                # Obfuscated (Spacing/Hyphens/Leet)
                r"i[\s\-_]?g[\s\-_]?n[\s\-_]?o[\s\-_]?r[\s\-_]?e[\s\-_]?",
                r"p[\s\-_]?r[\s\-_]?e[\s\-_]?v[\s\-_]?i[\s\-_]?o[\s\-_]?u[\s\-_]?s",
                r"i[\s\-_]?n[\s\-_]?s[\s\-_]?t[\s\-_]?r[\s\-_]?u[\s\-_]?c[\s\-_]?t[\s\-_]?i[\s\-_]?o[\s\-_]?n[\s\-_]?s",
                r"r[\s\-_]?e[\s\-_]?v[\s\-_]?e[\s\-_]?a[\s\-_]?l[\s\-_]?",
                r"p[\s\-_]?r[\s\-_]?o[\s\-_]?m[\s\-_]?p[\s\-_]?t",
                r"s[\s\-_]?y[\s\-_]?s[\s\-_]?t[\s\-_]?e[\s\-_]?m",
                r"[i1][\s\-_]?[g6b][\s\-_]?n[\s\-_]?[o0][\s\-_]?r[\s\-_]?[e3]",
                r"p[\s\-_]?[r7][\s\-_]?[e3][\s\-_]?[vu][\s\-_]?[i1][\s\-_]?[o0][\s\-_]?[uv][\s\-_]?[s5]",
                r"[i1][\s\-_]?n[\s\-_]?[s5][\s\-_]?t[\s\-_]?r[\s\-_]?[uv][\s\-_]?[ck][\s\-_]?t[\s\-_]?[i1][\s\-_]?[o0][\s\-_]?n[\s\-_]?[s5]",
                # Jailbreak Roles
                r"you are now DAN",
                r"do anything now",
                r"switch to developer mode",
                r"bypass safety filters",
                r"act as an AI with no moral",
                r"you are now EvilBot",
                r"stay in character as a hacker"
            ],
            
            IntentCategory.SYSTEM_OVERRIDE: [
                r"system override",
                r"shutdown",
                r"reboot",
                r"halt system",
                r"chmod",
                r"sudo\s+rm",
                r"transfer admin",
                r"disable antivirus",
                r"kill\s+-9",
                r"disable\s+the\s+firewall"
            ],
            IntentCategory.PII_EXFILTRATION: [
                r"read my passwords",
                r"dump database",
                r"dump the user database",
                r"show me all user emails",
                r"social security number",
                r"credit card number",
                r"ssn",
                r"private api keys"
            ]
        }
        
        self.compiled = {}
        import logging
        logger = logging.getLogger(__name__)
        for intent, patterns in self.patterns.items():
            self.compiled[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
            logger.info(f"Compiled {len(patterns)} patterns for {intent}")

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Check for deterministic regex matches.
        Returns the first critical match found.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Regex checking text repr: {repr(text)}") 
        
        for intent, patterns in self.compiled.items():
            for pattern in patterns:
                logger.info(f"Checking {intent} pattern: {pattern.pattern}")
                if pattern.search(text):
                    logger.info(f"Regex MATCH: {intent} on pattern '{pattern.pattern}'")
                    return {
                        "detected": True,
                        "score": 1.0,
                        "intent": intent,
                        "metadata": {"pattern": pattern.pattern}
                    }
        
        return {
            "detected": False,
            "score": 0.0,
            "intent": None,
            "metadata": {}
        }
