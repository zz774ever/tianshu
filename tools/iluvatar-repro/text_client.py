import argparse
import json
from pathlib import Path
import time

from openai import OpenAI


def main():
    parser = argparse.ArgumentParser(description='Text-only API and streaming validation')
    parser.add_argument('--base-url', default='http://127.0.0.1:18133/v1')
    parser.add_argument('--model', default='qwen')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--ready-timeout', type=float, default=1800)
    parser.add_argument('--require-quality', action='store_true')
    args = parser.parse_args()
    if args.ready_timeout <= 0:
        parser.error('--ready-timeout must be positive')
    root = Path(args.output_dir)
    if root.exists():
        parser.error('Output directory exists; use a new directory to preserve previous evidence')
    root.mkdir(parents=True)

    def save(name, value):
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    summary = {'transport_passed': False, 'quality_passed': False,
               'require_quality': args.require_quality, 'base_url': args.base_url,
               'scope': 'Text requests only; API functionality and two explicit quality checks'}
    try:
        client = OpenAI(api_key='EMPTY', base_url=args.base_url, timeout=300, max_retries=0)
        deadline = time.monotonic() + args.ready_timeout
        while True:
            try:
                models = client.models.list(timeout=5).model_dump()
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(5)
        save('models.json', models)
        assert any(value['id'] == args.model for value in models['data']), models
        request = dict(model=args.model,
                       messages=[{'role': 'user', 'content': 'Give me a short introduction to large language models.'}],
                       max_tokens=20, temperature=0.7, top_p=0.8, presence_penalty=1.5,
                       extra_body={'top_k': 20, 'chat_template_kwargs': {'enable_thinking': False}},
                       stream=True)
        save('stream-request.json', request)
        chunks = []
        content = []
        for chunk in client.chat.completions.create(**request):
            chunks.append(chunk.model_dump())
            if chunk.choices and chunk.choices[0].delta.content:
                content.append(chunk.choices[0].delta.content)
            save('stream-response.json', {'response': ''.join(content), 'chunks': chunks})
        response = ''.join(content)
        save('stream-response.json', {'response': response, 'chunks': chunks})
        assert response.strip(), 'Empty stream'
        assert any(choice.get('finish_reason') for chunk in chunks for choice in chunk['choices']), 'No stream finish marker'
        checks = []
        for question, expected in (
            ('What is 17 + 25? Answer only with the number.', '42'),
            ('What is the capital of France? Answer only the city name.', 'paris'),
        ):
            parameters = dict(model=args.model, messages=[{'role': 'user', 'content': question}],
                              max_tokens=32, temperature=0, top_p=1,
                              extra_body={'chat_template_kwargs': {'enable_thinking': False}})
            result = client.chat.completions.create(**parameters)
            text = result.choices[0].message.content or ''
            checks.append({'request': parameters, 'expected': expected, 'text': text,
                           'response': result.model_dump(),
                           'quality_passed': text.strip().rstrip('.。!').lower() == expected})
            save('deterministic-responses.json', checks)
            assert text.strip(), 'Empty non-stream response'
        summary.update(transport_passed=True,
                       quality_passed=all(value['quality_passed'] for value in checks),
                       stream_text=response, quality_checks=checks)
    except Exception as error:
        summary['error'] = f'{type(error).__name__}: {error}'
    passed = summary['transport_passed'] and (summary['quality_passed'] or not args.require_quality)
    summary['exit_code'] = 0 if passed else 1
    save('summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
