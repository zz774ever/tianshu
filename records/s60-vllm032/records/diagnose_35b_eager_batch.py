import asyncio
import copy
import json
import sys
from pathlib import Path

from openai import AsyncOpenAI

sys.path.insert(0, '/workspace/vllm-plugin-FL/tools/adaptation-gate-cases')
from case_utils import execute_request

ROOT = Path('/workspace/s60-adaptation')
SOURCE = ROOT / 'gate-results/35b-eager-ci-dispatch-single/Qwen3.6-35B-A3B/port-18101/text_single.json'
OUTPUT = ROOT / 'diagnostics/35b-eager-batch-context.json'


async def main():
    original = json.loads(SOURCE.read_text())
    request = original['input'][0]
    async with AsyncOpenAI(base_url='http://127.0.0.1:18101/v1', api_key='[REDACTED]', timeout=600) as client:
        results = await asyncio.gather(*[
            execute_request(client, copy.deepcopy(request), original['case']['served_model_name'])
            for request_index in range(2)
        ])
    report = {
        'kind': 'diagnostic_not_acceptance',
        'source': str(SOURCE),
        'input': request,
        'baseline': original['output'][0],
        'concurrent_results': results,
        'equal_to_baseline': [result['text'] == original['output'][0]['text'] for result in results],
        'concurrent_texts_equal': results[0]['text'] == results[1]['text'],
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'output': str(OUTPUT),
        'equal_to_baseline': report['equal_to_baseline'],
        'concurrent_texts_equal': report['concurrent_texts_equal'],
        'checks': [result['checks'] for result in results],
        'errors': [result.get('error') for result in results],
    }, indent=2), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
