import os
import json
import ollama

class Chat:
    def __init__(self, host: str = None, model: str = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama32-local")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client

    def teach_stream(self, question: str, topic: str = "", patterns: list = None):
        """
        Teach Mode: Clears doubts and explains concepts with step-by-step examples.
        Yields text chunks for a streamed HTTP response.
        """
        topic_context = ", ".join(patterns) if patterns else topic
        system_prompt = (
            f'You are a helpful and polite AI aptitude tutor teaching "{topic_context}".\n'
            'Follow these rules:\n'
            '1. Answer in a clear, concise, and easy-to-understand manner.\n'
            '2. Explain concepts using practical real-world examples.\n'
            '3. Always include a step-by-step solved example when relevant.\n'
            '4. Keep explanations focused and structured for optimal learning.'
        )

        try:
            stream = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                stream=True,
            )
            for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        except Exception as exc:
            yield (
                f"\n\nI could not reach the local Ollama server at {self.host}.\n"
                f"Please ensure Ollama is running. Error: {exc}"
            )

    def quiz(self, question: str, topic: str = "", patterns: list = None, num_questions: int = 5) -> dict:
        """
        Quiz Mode: Generates practice questions with choices, answer, and explanation.
        Returns a JSON-compatible dictionary (non-streamed).
        """
        topic_context = ", ".join(patterns) if patterns else topic
        system_prompt = (
            f'You are an AI aptitude quiz generator for topic "{topic_context}".\n'
            f'Generate {num_questions} practice questions with 4 choices, the correct answer, and an explanation.\n'
            'You MUST respond ONLY with a valid JSON object adhering strictly to this schema:\n'
            '{\n'
            '  "questions": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "description": "Question text here",\n'
            '      "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],\n'
            '      "answer": "Choice A",\n'
            '      "explanation": "Step-by-step solution explanation"\n'
            '    }\n'
            '  ]\n'
            '}\n'
            'Do not add markdown formatting or extra text outside the JSON object.'
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate practice questions for: {question}"},
                ],
                format="json",
                stream=False,
            )
            content = response.get("message", {}).get("content", "")

            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return {
                "error": "Failed to parse JSON quiz output",
                "details": str(exc),
                "raw_response": content if 'content' in locals() else ""
            }
        except Exception as exc:
            return {
                "error": f"Failed to connect to Ollama server at {self.host}",
                "details": str(exc)
            }

    def generate_response(self, question: str, mode: str = "teach", topic: str = "General aptitude", patterns: list = None):
        """
        Unified method to route AI response generation based on mode ('teach' vs 'quiz').
        """
        if mode.lower() == "quiz":
            return self.quiz(question=question, topic=topic, patterns=patterns)
        else:
            return self.teach_stream(question=question, topic=topic, patterns=patterns)


