"""Diagnostic only: compare real compiled subgraphs against the same FX graph."""
import copy
import itertools
import torch
from torch.utils._pytree import tree_map, tree_flatten
import vllm.compilation.compiler_interface as ci
counter = itertools.count()

def install(cls):
    original = cls.compile
    def compile_probe(self, graph, *args, **kwargs):
        reference = copy.deepcopy(graph)
        number = next(counter)
        compiled, handle = original(self, graph, *args, **kwargs)
        if compiled is None:
            return compiled, handle
        calls = 0
        def run(*inputs):
            nonlocal calls
            calls += 1
            if calls > 30 and calls % 28 != 0:
                return compiled(*inputs)
            cloned = tree_map(lambda x: x.clone() if isinstance(x, torch.Tensor) else x, inputs)
            with torch.no_grad():
                expected = reference(*cloned)
                actual = compiled(*inputs)
            aa, _ = tree_flatten(actual)
            bb, _ = tree_flatten(expected)
            for i, (a, b) in enumerate(zip(aa, bb)):
                if isinstance(a, torch.Tensor) and a.is_floating_point():
                    ac, bc = a.detach().float().cpu(), b.detach().float().cpu()
                    delta = (ac-bc).abs()
                    print('SUBGRAPH_DIFF', number, calls, i, list(a.shape), 'max', delta.max().item() if delta.numel() else 0, 'mean', delta.mean().item() if delta.numel() else 0, 'refmax', bc.abs().max().item() if bc.numel() else 0, flush=True)
                    if delta.numel() and torch.isfinite(delta).all() and delta.max() > 0.5:
                        torch.save({'actual':ac,'expected':bc,'graph':reference.code}, f'/workspace/s60-adaptation/subgraph-{number}-{calls}-{i}.pt')
            return actual
        return run, handle
    cls.compile = compile_probe
install(ci.InductorAdaptor)
install(ci.InductorStandaloneAdaptor)
