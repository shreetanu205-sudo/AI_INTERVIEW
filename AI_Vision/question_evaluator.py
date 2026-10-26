from dotenv import load_dotenv
from google import genai
import os
import json
from google.genai import errors
import time
import httpx

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"timeout": 10000}
)


def parse_response(text):
    """Parse and validate the evaluator's JSON response."""

    if not text or not isinstance(text, str):
        return None

    # Handle accidental Markdown fences from the model.
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(result, dict):
        return None

    required_fields = {
        "score",
        "feedback",
        "strengths",
        "weaknesses",
        "suggestion",
    }

    if not required_fields.issubset(result):
        return None

    score = result["score"]

    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 10
    ):
        return None

    for field in ("feedback", "suggestion"):
        if not isinstance(result[field], str):
            return None

    for field in ("strengths", "weaknesses"):
        if (
            not isinstance(result[field], list)
            or not all(
                isinstance(item, str) for item in result[field]
            )
        ):
            return None

    return {
        "score": float(score),
        "feedback": result["feedback"],
        "strengths": result["strengths"],
        "weaknesses": result["weaknesses"],
        "suggestion": result["suggestion"],
    }


def evaluate_answer(question, answer):
    """Evaluate one answer and return a validated result."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("The interview question is empty.")

    if not isinstance(answer, str) or not answer.strip():
        return {
            "score": 0.0,
            "feedback": "No answer was provided.",
            "strengths": [],
            "weaknesses": [
                "No response was provided to evaluate."
            ],
            "suggestion": (
                "Attempt the question and explain your reasoning "
                "using a relevant example."
            ),
        }

    prompt = f"""
You are an AI technical interview evaluator.

Evaluate the candidate's answer based on:
1. Technical correctness
2. Relevance to the question
3. Demonstrated understanding
4. Completeness appropriate to the question's difficulty

Be fair. A concise but correct answer can earn a high score.
Do not reward irrelevant content or penalize different wording.

INTERVIEW QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Return only a valid JSON object with exactly these keys:
{{
  "score": 8,
  "feedback": "Overall evaluation.",
  "strengths": ["Specific strength"],
  "weaknesses": ["Specific weakness"],
  "suggestion": "Actionable improvement advice."
}}

The score must be a number from 0 to 10.
The other fields must be strings or arrays of strings as shown.
Do not use Markdown fences or extra keys.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )

            raw_text = response.text
            result = parse_response(raw_text)

            if result is not None:
                print(
                    "Evaluation succeeded. "
                    f"Question score: {result['score']}/10"
                )
                return result

            print(
                "Evaluator returned invalid JSON or fields. "
                f"Attempt {attempt + 1}/3. "
                f"Raw response: {raw_text!r}"
            )

        except (
            errors.APIError,
            httpx.TimeoutException,
            httpx.ConnectError,
        ) as exc:
            print(
                f"Gemini API error on attempt "
                f"{attempt + 1}/3: {exc}"
            )

        if attempt < 2:
            time.sleep(2)

    # Do not turn an API or parsing failure into a fake score of zero.
    return None

print(parse_response(
    '{"score": 8, "feedback": "Good", '
    '"strengths": ["Correct"], '
    '"weaknesses": ["Incomplete"], '
    '"suggestion": "Add detail"}'
))

print(parse_response('{score: 8}'))
print(parse_response('["score", 8]'))

question = "What is inheritance in Java?"

answer = """
Inheritance is when a class gets things from another class.
It is related to OOP.
"""


result = evaluate_answer(question, answer)

print(result)

