
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


def generate_question(
    role,
    skills,
    experience,
    difficulty,
    question_type,
    previous_evaluation=None,
    previous_question=None
):
    prompt = f"""
You are an expert technical interviewer.

Generate exactly ONE interview question using these details:

Role: {role}
Skills: {", ".join(skills)}
Experience: {experience}
Difficulty: {difficulty}
Question type: {question_type}

Rules:
1. Make the question relevant to the role and skills.
2. Follow the selected difficulty and question type.
3. Do not provide the answer or explanation.
4. Return only the question text.
"""

    # Adaptive question generation
    if previous_evaluation is not None:
        prompt += f"""

PREVIOUS QUESTION:
{previous_question or "Not provided"}

PREVIOUS EVALUATION:
{previous_evaluation}

Generate the next question based on the evaluation.

Adaptation rules:
- Score below 5: focus on foundational concepts and weaknesses.
- Score from 5 to 7: test the candidate's weak areas.
- Score above 7: explore deeper concepts or practical applications.
- Use the feedback, weaknesses, and suggestions to choose
  an appropriate topic.
- Do not repeat the previous question.
- Keep the question relevant to the selected role and skills.
- Return only one question, without its answer.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    if not response.text:
        raise ValueError("The model returned an empty question.")

    return response.text.strip()


# Run this file directly to test normal generation.

if __name__ == "__main__":
    try:
        test_evaluation = {
            "score": 3,
            "feedback": "The answer lacks technical depth.",
            "strengths": ["Understands basic Java syntax"],
            "weaknesses": [
                "Does not explain inheritance clearly"
            ],
            "suggestion": "Explain parent and child classes."
        }

        question = generate_question(
            role="Java Developer",
            skills=["Java", "Spring Boot", "SQL"],
            experience="2 years",
            difficulty="Medium",
            question_type="Technical",
            previous_evaluation=test_evaluation,
            previous_question="What is polymorphism in Java?"
        )

        print("\nAdaptive Interview Question:\n")
        print(question)

    except Exception as error:
        print(f"Question generation failed: {error}")

