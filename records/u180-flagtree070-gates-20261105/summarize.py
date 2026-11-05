import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = Path('/workspace/vllm-plugin-FL/tools/adaptation-gate-cases')
matrix = json.loads((ROOT / 'matrix.json').read_text())
assert len(matrix) == 4
reports = []
finish_reasons = Counter()
by_kind = {}
failures = []
for path in sorted((ROOT / 'results').glob('*/*/port-*/*.json')):
    document = json.loads(path.read_text())
    assert len(document['output']) == document['summary']['request_count']
    assert sum(bool(output['passed']) for output in document['output']) == document['summary']['passed_count']
    reports.append({
        'path': str(path.relative_to(ROOT)),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'scenario': document['case']['scenario'],
        'started_at': document['started_at'],
        'finished_at': document['finished_at'],
        **document['summary'],
    })
    for output in document['output']:
        counts = by_kind.setdefault(output['kind'], {'total': 0, 'passed': 0})
        counts['total'] += 1
        counts['passed'] += int(output['passed'])
        choices = output.get('response', {}).get('choices', [])
        finish_reasons.update(choice['finish_reason'] for choice in choices)
        if not output['passed']:
            failures.append({
                'path': str(path.relative_to(ROOT)),
                'request_id': output['request_id'],
                'text': output['text'],
                'error': output.get('error'),
                'failed_checks': [key for key, value in output['checks'].items() if not value],
            })
assert len(reports) == 20
assert sum(report['request_count'] for report in reports) == 104
source_files = [path for path in CASES.rglob('*') if path.is_file() and path.suffix in {'.py', '.sh', '.png'}]
source_commits = {}
source_status = {}
for name, directory in {
    'vllm': '/workspace/vllm',
    'plugin': '/workspace/vllm-plugin-FL',
    'FlagGems-vllm': '/workspace/FlagGems-vllm',
    'FlagGems': '/workspace/FlagGems',
}.items():
    source_commits[name] = subprocess.check_output(['git', '-C', directory, 'rev-parse', 'HEAD'], text=True).strip()
    source_status[name] = subprocess.check_output(['git', '-C', directory, 'status', '--porcelain'], text=True)
installed_operator = Path('/usr/local/lib/python3.12/site-packages/flaggems_vllm/ops/moe_align_block_size.py')
source_operator = Path('/workspace/FlagGems-vllm/src/flaggems_vllm/ops/moe_align_block_size.py')
assert installed_operator.read_bytes() == source_operator.read_bytes()
manifest = {
    'schema_version': 1,
    'date': '2026-11-05',
    'container': 'test_plugin_28',
    'flagtree': json.loads((ROOT / 'after.json').read_text())['packages']['flagtree'],
    'report_count': len(reports),
    'request_count': sum(report['request_count'] for report in reports),
    'passed_request_count': sum(report['passed_count'] for report in reports),
    'failed_request_count': sum(report['failed_count'] for report in reports),
    'passed_scenario_count': sum(report['passed'] for report in reports),
    'requests_by_kind': by_kind,
    'finish_reasons': dict(finish_reasons),
    'source_commits': source_commits,
    'source_status_after_tests': source_status,
    'diagnostic_operator': {
        'installed_path': str(installed_operator),
        'source_path': str(source_operator),
        'installed_and_source_match': True,
        'sha256': hashlib.sha256(installed_operator.read_bytes()).hexdigest(),
    },
    'source_files': [{'path': str(path.relative_to(CASES)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(source_files)],
    'reports': reports,
    'rounds': matrix,
    'failures': failures,
}
manifest['artifacts'] = [
    {'path': name, 'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
    for name in ['before.json', 'after.json', 'device-verification.json', 'installation-verification.json', 'terminal-observations.json', 'cleanup-verification.json', 'matrix.json', 'fingerprint.py', 'verify_device.py', 'verify_installation.py', 'run_matrix.py', 'summarize.py', 'ROLLBACK.md']
]
(ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({key: value for key, value in manifest.items() if key not in {'source_files', 'reports', 'rounds', 'artifacts'}}, indent=2, ensure_ascii=False))
