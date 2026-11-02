from pathlib import Path
source = Path('/workspace/s60-adaptation/check_serve.py').read_text()
assert '18080/v1/completions' in source
assert 'results-serve-eager.json' in source
source = source.replace('18080/v1/completions', '18081/v1/completions')
source = source.replace('results-serve-eager.json', 'results-serve-graph.json')
Path('/workspace/s60-adaptation/check_serve_graph.py').write_text(source)
