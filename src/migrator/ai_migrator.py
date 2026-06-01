"""Migrador basado en IA usando NVIDIA NIM API (Gemma 4 31B).

Envía código legacy a un LLM que genera la versión migrada al lenguaje destino.
Esto demuestra el enfoque central del proyecto: usar IA generativa para
la transformación de código legacy.
"""

import json
import os
import requests
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AIMigrationResult:
    """Resultado de una migración con IA."""
    source_code: str
    migrated_code: str
    source_language: str
    target_language: str
    model: str
    explanation: str
    success: bool
    error: str | None = None


# Prompts especializados por tipo de migración
MIGRATION_PROMPTS = {
    "cpp_to_rust": """You are an expert code migration assistant specializing in converting C++ code to safe, idiomatic Rust.

RULES:
- Convert ALL C++ constructs to their Rust equivalents
- Replace raw pointers with safe references (&, &mut) or smart pointers (Box, Rc, Arc)
- Replace new/delete with Rust ownership (Box::new, Vec, etc.)
- Convert classes/structs to Rust structs with impl blocks
- Convert #include to use statements
- Convert std::cout to println!()
- Convert for loops to Rust for..in syntax
- Use proper Rust error handling (Result, Option) instead of exceptions
- Add proper lifetime annotations where needed
- Make the code compile with `rustc --edition 2021`
- Output ONLY the migrated Rust code, no explanations

INPUT C++ CODE:
```cpp
{source_code}
```

OUTPUT (Rust code only, no markdown fences):""",

    "java8_to_java17": """You are an expert code migration assistant specializing in modernizing Java 8 code to Java 17+.

RULES:
- Use pattern matching for instanceof (Java 16+)
- Use text blocks for multi-line strings (Java 15+)  
- Use switch expressions with -> syntax (Java 14+)
- Use var for local variable type inference (Java 10+)
- Use List.of(), Set.of(), Map.of() instead of Arrays.asList() (Java 9+)
- Use records where appropriate (Java 16+)
- Use sealed classes where appropriate (Java 17+)
- Keep the same class name and package
- Make the code compile with javac --release 17
- Output ONLY the migrated Java code, no explanations

INPUT Java 8 CODE:
```java
{source_code}
```

OUTPUT (Java 17 code only, no markdown fences):""",

    "cobol_to_java": """You are an expert code migration assistant specializing in converting COBOL to modern Java 17.

RULES:
- Convert COBOL divisions to Java classes
- Convert WORKING-STORAGE to class fields
- Convert PROCEDURE DIVISION paragraphs to methods
- Convert PERFORM to method calls
- Convert COBOL data types (PIC 9, PIC X) to Java types (int, String)
- Convert MOVE to assignment
- Convert IF/EVALUATE to if/switch
- Convert DISPLAY to System.out.println
- Use modern Java 17 features (records, sealed, pattern matching)
- Make the code compile with javac --release 17
- Output ONLY the migrated Java code, no explanations

INPUT COBOL CODE:
```cobol
{source_code}
```

OUTPUT (Java 17 code only, no markdown fences):""",

    "cobol_to_rust": """You are an expert code migration assistant specializing in converting COBOL to safe, modern Rust.

RULES:
- Convert COBOL divisions to Rust modules/structs
- Convert WORKING-STORAGE to struct fields
- Convert PROCEDURE DIVISION paragraphs to functions
- Convert PERFORM to function calls
- Convert COBOL data types (PIC 9, PIC X) to Rust types (i32, String)
- Convert MOVE to let assignments
- Convert IF/EVALUATE to if/match
- Convert DISPLAY to println!()
- Use proper Rust error handling (Result, Option)
- Make the code compile with `rustc --edition 2021`
- Output ONLY the migrated Rust code, no explanations

INPUT COBOL CODE:
```cobol
{source_code}
```

OUTPUT (Rust code only, no markdown fences):""",
}


class AIMigrator:
    """Migrador de código usando IA (NVIDIA NIM API)."""

    DEFAULT_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.model = model or os.environ.get("NVIDIA_MODEL", "meta/llama-4-maverick-17b-128e-instruct")
        self.api_url = os.environ.get("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")

    def migrate(
        self,
        source_code: str,
        migration_type: str,
        temperature: float = 0.3,
        max_tokens: int = 16384,
    ) -> AIMigrationResult:
        """Migrate code using the LLM.
        
        Args:
            source_code: The source code to migrate
            migration_type: One of 'cpp_to_rust', 'java8_to_java17', 'cobol_to_java', 'cobol_to_rust'
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        if migration_type not in MIGRATION_PROMPTS:
            return AIMigrationResult(
                source_code=source_code,
                migrated_code="",
                source_language=migration_type.split("_to_")[0],
                target_language=migration_type.split("_to_")[-1],
                model=self.model,
                explanation="",
                success=False,
                error=f"Tipo de migración no soportado: {migration_type}. "
                      f"Opciones: {list(MIGRATION_PROMPTS.keys())}",
            )

        prompt = MIGRATION_PROMPTS[migration_type].format(source_code=source_code)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a code migration expert. Output ONLY code, no explanations or markdown fences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=300,
            )

            if response.status_code != 200:
                return AIMigrationResult(
                    source_code=source_code,
                    migrated_code="",
                    source_language=migration_type.split("_to_")[0],
                    target_language=migration_type.split("_to_")[-1],
                    model=self.model,
                    explanation="",
                    success=False,
                    error=f"API error {response.status_code}: {response.text[:500]}",
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Clean up response - remove markdown fences if present
            migrated_code = self._clean_code_response(content)

            source_lang = migration_type.split("_to_")[0]
            target_lang = migration_type.split("_to_")[-1]

            return AIMigrationResult(
                source_code=source_code,
                migrated_code=migrated_code,
                source_language=source_lang,
                target_language=target_lang,
                model=self.model,
                explanation=f"Migrado con {self.model} via NVIDIA NIM API",
                success=True,
            )

        except requests.exceptions.Timeout:
            return AIMigrationResult(
                source_code=source_code,
                migrated_code="",
                source_language=migration_type.split("_to_")[0],
                target_language=migration_type.split("_to_")[-1],
                model=self.model,
                explanation="",
                success=False,
                error="Timeout: la API tardó más de 300 segundos en responder",
            )
        except Exception as e:
            return AIMigrationResult(
                source_code=source_code,
                migrated_code="",
                source_language=migration_type.split("_to_")[0],
                target_language=migration_type.split("_to_")[-1],
                model=self.model,
                explanation="",
                success=False,
                error=f"Error: {str(e)}",
            )

    def _clean_code_response(self, content: str) -> str:
        """Remove markdown code fences and thinking tags from LLM response."""
        lines = content.strip().split("\n")

        # Remove <think>...</think> blocks
        cleaned_lines = []
        in_think = False
        for line in lines:
            if "<think>" in line:
                in_think = True
                continue
            if "</think>" in line:
                in_think = False
                continue
            if not in_think:
                cleaned_lines.append(line)

        content = "\n".join(cleaned_lines).strip()

        # Remove markdown fences
        if content.startswith("```"):
            first_newline = content.index("\n")
            content = content[first_newline + 1:]
        if content.endswith("```"):
            content = content[:-3].rstrip()

        return content.strip()

    def migrate_file(
        self,
        input_path: Path,
        output_path: Path,
        migration_type: str,
    ) -> AIMigrationResult:
        """Migrate a file using AI."""
        source_code = input_path.read_text(encoding="utf-8")
        result = self.migrate(source_code, migration_type)

        if result.success:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.migrated_code, encoding="utf-8")

        return result
