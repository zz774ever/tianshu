import asyncio
import json
import os
import sys
from pathlib import Path

from openai import AsyncOpenAI

sys.path.insert(0, "/opt/vllm-plugin-FL/tools/adaptation-gate-cases")
from case_utils import TEXT_TASKS, quality_checks


async def main():
    destination = Path(os.environ.get("DIAG_RESULTS", "/results/quality-diagnosis/requests.json"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    results = []
    port = os.environ.get("DIAG_PORT", "8145")
    async with AsyncOpenAI(base_url=f"http://127.0.0.1:{port}/v1", api_key="EMPTY", timeout=600, max_retries=0) as client:
        async def request(round_name, index):
            prompt, required = TEXT_TASKS[index]
            response = await client.chat.completions.create(
                model="qwen-gate",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=32,
                logprobs=True,
                top_logprobs=5,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            text = response.choices[0].message.content or ""
            record = {
                "round": round_name,
                "index": index,
                "prompt": prompt,
                "text": text,
                "checks": quality_checks(text, list(required)),
                "strict_number": text.strip() == required[0] if index in (0, 3, 6) else None,
                "response": response.model_dump(mode="json"),
            }
            results.append(record)
            destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({key: record[key] for key in ("round", "index", "text", "strict_number")}), flush=True)

        await request("single-before", 0)
        for round_index in range(3):
            await asyncio.gather(*(request(f"batch-{round_index}", index) for index in range(8)))
        if os.environ.get("DIAG_EXTENDED") == "1":
            await asyncio.gather(*(request("reversed", index) for index in reversed(range(8))))
            await asyncio.gather(*(request("arithmetic-last", index) for index in (*range(1, 8), 0)))
            await asyncio.gather(*(request("identical-arithmetic", 0) for _ in range(8)))
        await request("single-after", 0)


asyncio.run(main())
