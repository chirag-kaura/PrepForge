from backend.app.llm.client import client
import time

def generate_question(
        subject: str, 
        topic: str = "",
        difficulty: str = "Medium",
        ) -> str:

    allowed_subjects =  ["SQL", "Machine Learning", "Statistics", "Python"]
    allowed_difficulties = ["Easy", "Medium", "Hard"]

    if subject not in allowed_subjects:
        raise ValueError(f"Invalid subject: {subject}. Allowed subjects are: {allowed_subjects}")

    if difficulty not in allowed_difficulties:
        raise ValueError(f"Invalid difficulty: {difficulty}. Allowed difficulties are: {allowed_difficulties}")

    if topic and len(topic)>200:
        raise ValueError("Topic length exceeds 200 characters. Please provide a shorter topic.")

    blocked_patterns = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the system prompt",
    "reveal your system prompt",
    "show your system prompt",
    "jailbreak",
    ]

    if topic and any(pattern in topic.lower() for pattern in blocked_patterns):
        raise ValueError("Invalid topic.")  

    start_time = time.perf_counter()
    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",
        messages=[
    {
        "role": "system",
        "content": (
            "You are an expert technical interview question generator. "
            "Generate high-quality interview questions that match the requested "
            "subject, topic, and difficulty. "
            "Difficulty guidelines: Easy tests fundamental concepts, "
            "Medium tests practical application and moderate reasoning, "
            "Hard tests advanced concepts, edge cases, optimization, or complex reasoning."
        ),
    },
    {
        "role": "user",
        "content": (
            f"Generate exactly ONE {difficulty.lower()}-difficulty "
            f"interview question for {subject}. "
            f"{f'Focus specifically on the topic: {topic}. ' if topic else ''}"
            "The question should be clear, relevant, and suitable for an interview. "
            "Return ONLY the question text. "
            "Do not provide an answer, explanation, hints, title, numbering, "
            "Markdown, or additional text."
        ),
    },
    ],
)

    question = response.choices[0].message.content.strip()

    if not question:
        raise ValueError("LLM returned an empty question.")

    if len(question) > 1000:
        raise ValueError("LLM returned an excessively long question.")

    if len(question.split()) < 5:
        raise ValueError("LLM returned an invalid question.")

    latency = time.perf_counter() - start_time
    print(f"LLM latency: {latency:.2f} seconds")

    return question, latency