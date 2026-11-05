import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'manifest.json').read_text())
lines = [
    '# FlagTree 0.7 四轮测试完整输入与输出',
    '',
    '容器：`test_plugin_28`；日期：2026-11-05。20 个原始场景，共 104 条请求。',
    '',
    '本页保留全部题目和模型回答，不截断。原始 API 响应、usage、检查和耗时另见每节链接的 JSON；图片使用原始本地路径。没有保存完整服务终端日志，终端诊断只有单独的观察记录。',
    '',
]
request_count = 0
for entry in manifest['reports']:
    path = ROOT / entry['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    report = json.loads(path.read_text())
    round_name = path.relative_to(ROOT).parts[1]
    lines.extend([
        f'## {round_name} / {report["case"]["scenario"]}', '',
        f'[完整原始 JSON]({entry["path"]})', '',
    ])
    requests = {item['request_id']: item for item in report['input']}
    for output in report['output']:
        request_count += 1
        request = requests[output['request_id']]
        lines.extend([
            f'### {output["request_id"]}', '',
            '完整输入：', '', '````json',
            json.dumps(request, ensure_ascii=False, indent=2), '````', '',
            '完整回答：', '', '````text', output['text'], '````', '',
            '检查与响应统计：', '', '````json',
            json.dumps({
                'passed': output['passed'],
                'latency_seconds': output['latency_seconds'],
                'checks': output['checks'],
                'finish_reason': output['response']['choices'][0]['finish_reason'],
                'usage': output['response']['usage'],
            }, ensure_ascii=False, indent=2), '````', '',
        ])
assert request_count == 104
(ROOT / 'full-output.md').write_text('\n'.join(lines).rstrip() + '\n')
archive_path = ROOT / 'complete-results.zip'
with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.name in {'complete-results.zip', 'complete-results.sha256'}:
            continue
        relative = path.relative_to(ROOT)
        if '__pycache__' in relative.parts:
            continue
        info = zipfile.ZipInfo(str(relative), date_time=(2026, 11, 5, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, path.read_bytes())
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    for entry in manifest['reports']:
        assert hashlib.sha256(archive.read(entry['path'])).hexdigest() == entry['sha256']
digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
(ROOT / 'complete-results.sha256').write_text(digest + '  complete-results.zip\n')
print(json.dumps({'requests_exported': request_count, 'zip_bytes': archive_path.stat().st_size, 'zip_sha256': digest}))
