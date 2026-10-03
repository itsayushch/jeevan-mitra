"""Manually benchmark the configured neural voice without beneficiary data."""
import asyncio
import time
import edge_tts


async def main():
    for voice, text in [('en-IN-NeerjaNeural', 'Hello, I am JeevanMitra. What work do you do?'),
                        ('hi-IN-SwaraNeural', 'नमस्ते, मैं जीवनमित्र हूँ। आप अभी क्या काम करते हैं?')]:
        start = time.perf_counter()
        first = None
        size = 0
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk['type'] == 'audio':
                first = first or time.perf_counter() - start
                size += len(chunk['data'])
        print(voice, {'first_audio_seconds': round(first or 0, 2),
                      'total_seconds': round(time.perf_counter() - start, 2), 'bytes': size})


if __name__ == '__main__':
    asyncio.run(main())
