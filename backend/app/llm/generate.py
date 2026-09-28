from backend.app.llm.client import client

def generate_question(subject: str) -> str:
    response = client.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages = [
            {
                "role": "system",
                "content": "You are an interview question generator."
            },
            {
                "role": "user",
                "content": f"Generate exactly one interview question for {subject}. Return only the question text, without a title, explanation, or Markdown formatting."
            }
        ]
    )

    return response.choices[0].message.content