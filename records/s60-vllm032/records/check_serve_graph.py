"""Exercise actual OpenAI HTTP completion, streaming and concurrency."""
import concurrent.futures
import json
import urllib.request
from pathlib import Path

URL = 'http://127.0.0.1:18081/v1/completions'

def request(prompt, stream=False):
    body = json.dumps(dict(model='/models/Qwen3-0.6B', prompt=prompt,
                           temperature=0, max_tokens=16, stream=stream)).encode()
    req = urllib.request.Request(URL, body, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as response:
        assert response.status == 200
        if not stream:
            result = json.load(response)
            assert result['usage']['completion_tokens'] == 16, result
            return result
        text = ''
        done = False
        for line in response:
            if not line.startswith(b'data: '):
                continue
            data = line[6:].strip()
            if data == b'[DONE]':
                done = True
                break
            chunk = json.loads(data)
            text += chunk['choices'][0]['text']
        assert done and text, (done, text)
        return {'stream_text': text, 'done': done}

if __name__ == '__main__':
    prompts = ['The capital of France is', 'The quick brown fox jumps over the']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        outputs = list(pool.map(request, prompts))
    streamed = request(prompts[0], True)
    assert streamed['stream_text'] == outputs[0]['choices'][0]['text']
    result = {'concurrent': outputs, 'stream': streamed}
    path = Path('/workspace/s60-adaptation/results-serve-graph.json')
    path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, ensure_ascii=False))
