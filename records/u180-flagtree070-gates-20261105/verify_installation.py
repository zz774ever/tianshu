import hashlib
import json
import zipfile
from email.parser import Parser
from importlib import metadata
from pathlib import Path

import triton


ROOT = Path('/workspace/adaptation-gate-upgrade-20261105')
WHEELS = Path('/workspace/sources/flagtree-0.7.0-iluvatar')
distribution = metadata.distribution('flagtree')


def digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


wheel_details = []
new_hashes = {}
mismatches = []
for version in ['0.6.2a3+iluvatar3.6', '0.7.0+iluvatar3.6']:
    path = WHEELS / f'flagtree-{version}-cp312-cp312-linux_x86_64.whl'
    with path.open('rb') as stream:
        wheel_hash = digest(stream)
    with zipfile.ZipFile(path) as archive:
        package_metadata = Parser().parsestr(archive.read(f'flagtree-{version}.dist-info/METADATA').decode())
        version_line = next(line for line in archive.read('triton/__init__.py').decode().splitlines() if line.startswith('__version__'))
        details = {
            'filename': path.name,
            'sha256': wheel_hash,
            'distribution_name': package_metadata['Name'],
            'distribution_version': package_metadata['Version'],
            'summary': package_metadata['Summary'],
            'triton_version_assignment': version_line,
            'flagtree_init': archive.read('flagtree/__init__.py').decode(),
            'compiler_libraries': [],
        }
        if version == '0.7.0+iluvatar3.6':
            for name in archive.namelist():
                if name.endswith('/') or not name.startswith(('triton/', 'flagtree/')):
                    continue
                with archive.open(name) as stream:
                    expected = digest(stream)
                new_hashes[name] = expected
                installed = Path(distribution.locate_file(name))
                actual = None
                if installed.is_file():
                    with installed.open('rb') as stream:
                        actual = digest(stream)
                if expected != actual:
                    mismatches.append({'path': name, 'expected': expected, 'actual': actual})
        for name in archive.namelist():
            if name.startswith('triton/') and name.endswith('.so'):
                with archive.open(name) as stream:
                    library_hash = new_hashes.get(name) or digest(stream)
                details['compiler_libraries'].append({'path': name, 'sha256': library_hash})
        wheel_details.append(details)
report = {
    'distribution_version': distribution.version,
    'distribution_metadata_path': str(distribution._path),
    'triton_import_version': triton.__version__,
    'triton_import_path': triton.__file__,
    'installed_from': json.loads(distribution.read_text('direct_url.json')),
    'module_owners': {name: metadata.packages_distributions().get(name) for name in ['triton', 'flagtree']},
    'standalone_triton_distributions': [item.metadata['Name'] for item in metadata.distributions() if 'triton' in item.metadata.get('Name', '').lower()],
    'wheel_details': wheel_details,
    'installed_payload_files_checked': len(new_hashes),
    'installed_payload_mismatches': mismatches,
}
(ROOT / 'installation-verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(report, indent=2, ensure_ascii=False))
assert distribution.version == '0.7.0+iluvatar3.6'
assert len(new_hashes) > 0 and not mismatches
assert wheel_details[1]['sha256'] == 'af6a7c9eddf167441fd872c3e6d673e9da572608dee79dba655b0775db740176'
