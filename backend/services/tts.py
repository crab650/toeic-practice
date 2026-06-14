import asyncio

import edge_tts

from ..config import CACHE_DIR


VOICES = [
    'en-US-GuyNeural',
    'en-US-AriaNeural',
    'en-GB-RyanNeural',
    'en-GB-SoniaNeural',
    'en-AU-NatashaNeural',
    'en-AU-WilliamNeural',
]


async def generate_part2_audio(question_id, question, opt_a, opt_b, opt_c, filepath):
    voice = VOICES[question_id % len(VOICES)]
    text_content = (
        f"Number {question_id}. ... "
        f"{question} ... ... "
        f"(A) {opt_a} ... "
        f"(B) {opt_b} ... "
        f"(C) {opt_c}"
    )

    communicate = edge_tts.Communicate(text=text_content, voice=voice)
    await communicate.save(filepath)


def ensure_part2_audio(question_id, question_data, filepath):
    CACHE_DIR.mkdir(exist_ok=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            generate_part2_audio(
                question_id,
                question_data['question'],
                question_data['option_a'],
                question_data['option_b'],
                question_data['option_c'],
                filepath,
            )
        )
    finally:
        loop.close()
