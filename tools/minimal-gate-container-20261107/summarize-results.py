import json
from datetime import datetime
from pathlib import Path

root = Path('/workspace/minimal-gate-container-20261107/evidence')
rounds = []
expected = {'text_single': 1, 'text_concurrent_8': 8, 'image_single': 1,
            'image_concurrent_8': 8, 'mixed_concurrent_8': 8}
for model in ['Qwen3.6-27B', 'Qwen3.6-35B-A3B']:
    for mode in ['graph', 'eager']:
        directory = root / f'{model}-{mode}'
        exit_code = int((directory / 'exit-code.txt').read_text().strip())
        cases = {}
        failed_requests = []
        for path in sorted((directory / 'results').rglob('*.json')):
            document = json.loads(path.read_text())
            scenario = document['case']['scenario']
            assert scenario in expected and scenario not in cases
            assert document['summary']['request_count'] == expected[scenario]
            assert len(document['output']) == expected[scenario]
            assert sum(bool(item['passed']) for item in document['output']) == document['summary']['passed_count']
            cases[scenario] = document['summary']
            failed_requests.extend({'scenario': scenario, 'request_id': item['request_id'],
                                    'text': item.get('text'), 'error': item.get('error'),
                                    'checks': item.get('checks')}
                                   for item in document['output'] if not item['passed'])
        assert set(cases) == set(expected), (directory, cases)
        passed_count = sum(case['passed_count'] for case in cases.values())
        times = {name: (directory / f'{name}-at.txt').read_text().strip()
                 for name in ['started', 'ready', 'gate-finished', 'finished']}
        parsed = {name: datetime.fromisoformat(value) for name, value in times.items()}
        rounds.append({'model': model, 'mode': mode, 'requests': 26,
                       'passed_count': passed_count, 'exit_code': exit_code,
                       'passed': exit_code == 0 and passed_count == 26,
                       'failed_requests': failed_requests,
                       'times': times,
                       'startup_seconds': (parsed['ready'] - parsed['started']).total_seconds(),
                       'gate_seconds': (parsed['gate-finished'] - parsed['ready']).total_seconds(),
                       'total_seconds': (parsed['finished'] - parsed['started']).total_seconds(),
                       'cases': cases})
result = {'container_name': 'fl-gate-minimal-20261107',
          'plugin_commit': '7a94aeec80fbb795d5596569eb7d40cfe5460106',
          'system_python': True, 'virtual_environment': False,
          'requests': sum(item['requests'] for item in rounds),
          'passed_count': sum(item['passed_count'] for item in rounds),
          'all_passed': all(item['passed'] for item in rounds), 'rounds': rounds}
first_attempt = root / 'first-complete-summary.json'
if first_attempt.is_file():
    initial = json.loads(first_attempt.read_text())
    result['first_complete_run'] = {'requests': initial['requests'],
                                    'passed_count': initial['passed_count'],
                                    'all_passed': initial['all_passed']}
    result['known_quality_failure_observed'] = not initial['all_passed']
    result['known_quality_failure_root_cause_resolved'] = False
    result['first_attempt_failed_requests'] = [
        dict(item, model=round_result['model'], mode=round_result['mode'])
        for round_result in initial['rounds'] for item in round_result['failed_requests']]
    result['executed_gate_requests_including_repeat'] = result['requests'] + 26
assert result['requests'] == 104
(root / 'final-summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
