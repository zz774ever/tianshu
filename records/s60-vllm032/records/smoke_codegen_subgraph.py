"""Compare compiled subgraphs after production dtype-ABI correction."""
import subgraph_probe
import runpy

if __name__ == '__main__':
    runpy.run_path('/workspace/s60-adaptation/smoke.py', run_name='__main__')
