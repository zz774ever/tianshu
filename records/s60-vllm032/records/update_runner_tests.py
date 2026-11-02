from pathlib import Path
p=Path('/workspace/vllm-plugin-FL/tests/unit_tests/worker/test_model_runner.py')
s=p.read_text()
a=s.index('# =============================================================================\n# Layer 2: _pad_for_sequence_parallelism Logic Tests')
b=s.index('# =============================================================================\n# Layer 2: _get_positions Routing Tests',a)
s=s[:a]+s[b:]
s=s.replace('''        # XDRoPE positions (2D)
        mock_runner.xdrope_positions = MagicMock()
        mock_runner.xdrope_positions.gpu = torch.arange(200).reshape(2, 100)

''','')
s=s.replace('        mock_runner.uses_xdrope_dim = 0\n','')
a=s.index('    def test_xdrope_returns_2d_positions(')
b=s.find('\n    def ',a+5)
if b == -1:
 b=s.find('\n# ===',a)
if b == -1:
 b=len(s)
s=s[:a]+'''    def test_mrope_returns_indexed_positions(self, mock_model_runner):
        """0.32 routes indexed multimodal positions through MRoPE."""
        mock_model_runner.uses_mrope = True
        indices = torch.tensor([15, 0, 99, 5])
        result = mock_model_runner._get_positions(indices)
        expected = mock_model_runner.mrope_positions.gpu[:, indices]
        assert result.shape == (3, 4)
        torch.testing.assert_close(result, expected)
'''+s[b:]
p.write_text(s)
print('Updated removed 0.28 private helper tests and MRoPE indexed coverage')
