from pathlib import Path
p = Path('/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/gcu/impl/attention.py')
s = p.read_text().replace('    get_kv_cache_layout,\n', '')
start = s.index('    @staticmethod\n    def get_kv_cache_shape(')
end = s.index('    @classmethod\n    def supports_head_size', start)
s = s[:start] + s[end:]
p.write_text(s)
