from backend.app.llm.client import client
import time


def generate_question(
        subject: str, 
        topic: str = "",
        difficulty: str = "Medium",
        ) -> str:
    start_time = time.perf_counter()
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are an interview question generator."
            },
            {
                "role": "user",
                "content": (
                    f"Generate exactly one {difficulty.lower()} difficulty interview question "
                    f"for {subject}. "
                    f"{f'Focus specifically on the topic: {topic}. ' if topic else ''}"
                    "Return only the question text, without a title, explanation, "
                    "or Markdown formatting."
                )
            }
        ],
    )

    latency = time.perf_counter() - start_time
    print(f"LLM latency: {latency:.2f} seconds")    

    return response.choices[0].message.content