from pathlib import Path
p=Path('/workspace/vllm-plugin-FL/docker/enflame/README.md')
s=p.read_text()
changes={
'and installs the official vLLM 0.28.0 empty-device':'and installs the official vLLM 0.32.0 empty-device',
'--image-name local/vllm-plugin-fl --image-tag v0.28.0-enflame-candidate':'--image-name local/vllm-plugin-fl --image-tag v0.32.0-enflame-candidate',
'`v0.28.0-enflame-ci` or `v0.28.0-enflame-dev`. This command does not push.':'the branch defaults from `docker/build.sh`. Pass the explicit candidate tag\nabove when building 0.32. This command does not push.',
'commit; the default official v0.28.0 commit is\n`2cf0a6915ce544dc493a0990f2ea38d81601128a`.':'commit; the default official v0.32.0 commit is\n`5df63a7203cdb9328d824a27b682e77c7b9928be`.',
'The 2026-10-13 dependency image was validated on S60':'## Historical 0.28 image validation\n\nThe 2026-10-13 dependency image was validated on S60',
}
for old,new in changes.items():
    assert old in s, old
    s=s.replace(old,new,1)
p.write_text(s)
