"""Capture first real Qwen3 prefill, identified by actual token IDs."""
import os
import functools
from pathlib import Path
import torch
from vllm.model_executor.models.qwen3 import Qwen3ForCausalLM

_init = Qwen3ForCausalLM.__init__
_forward = Qwen3ForCausalLM.forward
_active = False
_done = False
_data = {}
_real_calls = 0
_target_call = int(os.environ.get('CAPTURE_LAYERS_CALL', '1'))


def cpu(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, (tuple, list)):
        return tuple(cpu(v) for v in value)
    return None


@functools.wraps(_init)
def init(self, *args, **kwargs):
    _init(self, *args, **kwargs)
    for name, module in self.named_modules():
        boundary = name.startswith('model.layers.') and name.count('.') == 2
        detail_layer = int(os.environ.get('CAPTURE_DETAIL_LAYER', '0'))
        detail = name.startswith(f'model.layers.{detail_layer}.')
        if boundary or detail or name in ('model.embed_tokens', 'model.norm'):
            def before(mod, inputs, key=name):
                if _active:
                    _data[key] = {'input': cpu(inputs)}
                    if os.environ.get('CAPTURE_RMS_CONTEXT') and key.endswith('post_attention_layernorm'):
                        _data[key]['context'] = {
                            'weight': cpu(mod.weight),
                            'epsilon': mod.variance_epsilon,
                            'inference': torch.is_inference_mode_enabled(),
                            'grad': torch.is_grad_enabled(),
                            'input_stride': tuple(inputs[0].stride()),
                            'residual_stride': tuple(inputs[1].stride()),
                            'input_offset': inputs[0].storage_offset(),
                            'residual_offset': inputs[1].storage_offset(),
                            'forward': str(mod._forward_method),
                        }
            def hook(mod, inputs, output, key=name):
                if _active:
                    _data[key]['output'] = cpu(output)
                    if os.environ.get('CAPTURE_RMS_CONTEXT') and key == 'model.layers.6.post_attention_layernorm':
                        from vllm_fl.dispatch.backends.vendor.gcu.impl.normalization import rms_norm_gcu
                        _data[key]['repeat_actual'] = cpu(rms_norm_gcu(mod, *inputs))
                        cloned = tuple(t.clone() for t in inputs)
                        _data[key]['repeat_clone'] = cpu(rms_norm_gcu(mod, *cloned))
            module.register_forward_pre_hook(before)
            module.register_forward_hook(hook)


@functools.wraps(_forward)
def forward(self, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):
    global _active, _done, _data, _real_calls
    real = not _done and input_ids is not None and bool((input_ids != 0).any().item())
    if real:
        _real_calls += 1
    target_pos = os.environ.get('CAPTURE_LAYERS_POSITION')
    target_id = os.environ.get('CAPTURE_LAYERS_TOKEN')
    if real and target_pos is not None and target_id is not None:
        should = bool(((positions == int(target_pos)) &
                       (input_ids == int(target_id))).any().item())
    else:
        should = real and _real_calls == _target_call
    _active = should
    if should:
        _data = {'input_ids': cpu(input_ids), 'positions': cpu(positions)}
    try:
        out = _forward(self, input_ids, positions, intermediate_tensors, inputs_embeds)
        if should:
            _data['result'] = cpu(out)
            torch.save(_data, Path(os.environ['CAPTURE_LAYERS_PATH']))
            _done = True
        return out
    finally:
        _active = False


Qwen3ForCausalLM.__init__ = init
Qwen3ForCausalLM.forward = forward
