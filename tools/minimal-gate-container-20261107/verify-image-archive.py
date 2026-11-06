import hashlib
import json
import sys
import tarfile
from pathlib import Path

root = Path('/workspace/minimal-gate-container-20261107')
path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'artifacts/iluvatar-gate-pr674-7a94aee-gems55-20261107.tar'
with tarfile.open(path, 'r:') as archive:
    manifest = json.load(archive.extractfile('manifest.json'))
    assert len(manifest) == 1
    image = manifest[0]
    config_bytes = archive.extractfile(image['Config']).read()
    image_id = 'sha256:' + hashlib.sha256(config_bytes).hexdigest()
    expected_id = (root / 'evidence/packaged-image-id.txt').read_text().strip()
    assert image_id == expected_id
    config = json.loads(config_bytes)
    assert config['config']['WorkingDir'] == '/opt/gate'
    assert config['config']['Labels']['io.flagos.gate.known-quality-failure'] == 'true'
    with tarfile.open(fileobj=archive.extractfile(image['Layers'][-1]), mode='r:') as layer:
        members = {member.name.removeprefix('./'): member for member in layer.getmembers()}
        required = [
            'opt/gate/gate-env.sh', 'opt/gate/validation-summary.json',
            'opt/vllm-plugin-FL/tools/adaptation-gate-cases/run_test.sh',
            'opt/FlagCX/build/lib/libflagcx.so',
            'opt/FlagCX/plugin/interservice/flagcx_wrapper.py',
        ]
        assert all(name in members for name in required)
        excluded_prefixes = ['models/', 'results/', 'input/', 'run/iluvatar-host-driver/']
        unexpected = [name for name, member in members.items()
                      if member.isfile() and any(name.startswith(prefix) for prefix in excluded_prefixes)]
        assert not unexpected, unexpected
        report = json.load(layer.extractfile(members['opt/gate/validation-summary.json']))
        assert report['requests'] == 104 and report['passed_count'] == 104
        assert report['known_quality_failure_observed']
        assert not report['known_quality_failure_root_cause_resolved']
result = {'archive': path.name, 'bytes': path.stat().st_size, 'image_id': image_id,
          'layers': len(image['Layers']), 'required_container_files_present': required,
          'external_mount_contents_absent_from_new_layer': True,
          'validation_summary_preserves_known_issue': True}
(root / 'evidence/packaged-image-archive-verification.json').write_text(
    json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
