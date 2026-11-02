from torch._inductor.graph import GraphLowering
from torch_gcu.gcu.inductor import backend_register
from vllm_fl.dispatch.backends.vendor.gcu.impl.inductor import _loaded_gcu_inductor_providers
for provider in _loaded_gcu_inductor_providers(backend_register):
    provider.GCUCompileHelper.compile_to_module=staticmethod(GraphLowering._compile_to_module)
