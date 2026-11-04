# 本轮完整命令索引

所有条目在容器 a20ad38e000a 执行。完整 stdout/stderr、起止时间、tee 退出码和辅助指纹见 raw-steps.tar.gz；此处保留逐条命令和实际退出码。

安装/启动流程已结束后生成本索引。失败及启动尚未就绪的检查均保留，不能按最后一条命令覆盖此前结果。

## 20261104T132323Z-check-official-github-image-wD3oSk

退出码：`0`

```bash
python3 -c $'import base64\nfrom concurrent.futures import ThreadPoolExecutor\nimport hashlib\nimport json\nimport urllib.error\nimport urllib.request\nroot = "https://api.github.com/repos/flagos-ai/vllm-plugin-FL"\ndef get(url):\n    request = urllib.request.Request(url, headers={"User-Agent": "iluvatar-image-provenance-check", "Accept": "application/vnd.github+json"})\n    with urllib.request.urlopen(request, timeout=30) as response:\n        return json.load(response)\nrepository = get(root)\nbranch = repository["default_branch"]\nprint("OFFICIAL_REPOSITORY", repository["html_url"], "DEFAULT_BRANCH", branch, flush=True)\nreference = get(root + "/commits/" + branch)\ncommit = reference["sha"]\nprint("OFFICIAL_HEAD", commit, flush=True)\npaths = ["docs/usage/iluvatar.md", ".github/configs/iluvatar.yml", "docker/iluvatar/Dockerfile"]\ndef inspect(path):\n    try:\n        result = get(root + "/contents/" + path + "?ref=" + commit)\n        data = base64.b64decode(result["content"]).decode()\n        lines = data.splitlines()\n        matched = set()\n        for index, line in enumerate(lines):\n            if any(term in line.lower() for term in ("eb904d40", "v0.28.0-iluvatar-ci", "libixthunk", "libcuda", "libixml", "corex", "from ", "venv", "prebuilt", "image digest")):\n                matched.update(range(max(0,index-1),min(len(lines),index+3)))\n        return {"path": path, "url": result["html_url"], "sha": result["sha"], "lines": [f"{index+1}: {lines[index]}" for index in sorted(matched)]}\n    except Exception as error:\n        return {"path": path, "error": str(error)}\nwith ThreadPoolExecutor(max_workers=3) as pool:\n    for result in pool.map(inspect, paths):\n        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)\n'
```

## 20261104T132345Z-check-official-registry-manifest-BWYR1g

退出码：`1`

```bash
python3 -c $'import hashlib\nimport json\nimport re\nimport urllib.error\nimport urllib.parse\nimport urllib.request\nroot = "https://harbor.baai.ac.cn"\nrepository = "plugin/vllm-plugin-fl"\ntag = "v0.28.0-iluvatar-ci"\nexpected = "sha256:eb904d40a92e9769f358f4d81c8043acfbc30b1b077f0a31210be6316ec0cf18"\nheaders = {"User-Agent": "iluvatar-image-provenance-check", "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json"}\nurl = root + "/v2/" + repository + "/manifests/" + tag\ndef fetch():\n    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30)\ntry:\n    try:\n        response = fetch()\n    except urllib.error.HTTPError as error:\n        if error.code != 401:\n            raise\n        challenge = error.headers.get("WWW-Authenticate", "")\n        print("REGISTRY_AUTH_CHALLENGE", challenge, flush=True)\n        fields = dict(re.findall(r\'(\\w+)="([^"]*)"\', challenge))\n        realm = fields.get("realm", "")\n        assert realm.startswith("https://harbor.baai.ac.cn/"), realm\n        query = urllib.parse.urlencode({"service": fields.get("service", "harbor-registry"), "scope": fields.get("scope", "repository:" + repository + ":pull")})\n        with urllib.request.urlopen(realm + "?" + query, timeout=30) as token_response:\n            payload = json.load(token_response)\n        token = payload.get("token") or payload.get("access_token")\n        assert token\n        headers["Authorization"] = "Bearer " + token\n        response = fetch()\n    with response:\n        raw = response.read()\n        digest = response.headers.get("Docker-Content-Digest") or "sha256:" + hashlib.sha256(raw).hexdigest()\n        manifest = json.loads(raw)\n        print(json.dumps({"registry": root, "repository": repository, "tag": tag, "current_digest": digest, "expected_digest": expected, "matches_expected": digest == expected, "mediaType": manifest.get("mediaType"), "config_digest": manifest.get("config", {}).get("digest"), "manifests": manifest.get("manifests")}, indent=2), flush=True)\nexcept Exception as error:\n    print("REGISTRY_CHECK_UNAVAILABLE", type(error).__name__, str(error), flush=True)\n    raise SystemExit(1)\n'
```

## 20261104T132423Z-check-official-main-dev-config-abTOLV

退出码：`0`

```bash
python3 -c $'import base64\nfrom concurrent.futures import ThreadPoolExecutor\nimport json\nimport urllib.request\nroot = "https://api.github.com/repos/flagos-ai/vllm-plugin-FL"\ndef get(path):\n    with urllib.request.urlopen(urllib.request.Request(root + path, headers={"User-Agent": "iluvatar-image-provenance-check"}), timeout=25) as response:\n        return json.load(response)\ndef inspect(item):\n    ref,path = item\n    try:\n        result = get("/contents/" + path + "?ref=" + ref)\n        data = base64.b64decode(result["content"]).decode()\n        if path.endswith("iluvatar.yml"):\n            selected = [f"{index}: {line}" for index,line in enumerate(data.splitlines(),1)]\n        else:\n            terms = ("v0.28.0-iluvatar-ci", "eb904d40", "iluvatar-corex", "ci_image")\n            selected = [f"{index}: {line}" for index,line in enumerate(data.splitlines(),1) if any(term in line for term in terms)]\n        return {"ref": ref, "path": path, "url": result["html_url"], "lines": selected}\n    except Exception as error:\n        return {"ref":ref,"path":path,"error":str(error)}\nitems = [("main",".github/configs/iluvatar.yml"), ("0.5.0-dev",".github/configs/iluvatar.yml"), ("0.5.0-dev","docs/usage/iluvatar.md"), ("0.5.0-dev","docker/iluvatar/Dockerfile")]\nwith ThreadPoolExecutor(max_workers=4) as pool:\n    for result in pool.map(inspect,items):\n        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)\n'
```

## 20261104T132832Z-diagnose-driver-library-provenance-NQXyoT

退出码：`0`

```bash
python -c $'import hashlib\nimport os\nfrom pathlib import Path\nimport subprocess\nimport sys\nprint("LD_LIBRARY_PATH", os.environ.get("LD_LIBRARY_PATH"), flush=True)\npaths = ["/usr/local/corex/lib64/libcuda.so.1", "/usr/local/corex/lib64/libixml.so",\n         "/workspace/repro/driver-extracted/corex/lib64/libcuda.so.1",\n         "/workspace/repro/driver-extracted/corex/lib64/libixthunk.so"]\nfor name in paths:\n    path = Path(name)\n    print("LIBRARY", name, "exists", path.exists(), flush=True)\n    if path.is_file():\n        print("SHA256", hashlib.sha256(path.read_bytes()).hexdigest(), flush=True)\n        if path.name == "libcuda.so.1":\n            baseline = dict(os.environ)\n            baseline.pop("LD_LIBRARY_PATH", None)\n            for label, environment in (("IMAGE_DEFAULT_PATH", baseline), ("CURRENT_PATH", dict(os.environ))):\n                result = subprocess.run(["ldd", name], env=environment, text=True, capture_output=True)\n                print(label, result.returncode, result.stdout, result.stderr, flush=True)\nprint("OTHER_IXTHUNK_FILES", flush=True)\nfor root in (Path("/usr/local/corex"), Path("/usr/local/lib")):\n    if root.exists():\n        for path in root.rglob("libixthunk.so*"):\n            print(path, flush=True)\nprint("GPU_PROBE", flush=True)\nimport torch\nprint("torch", torch.__version__, "available", torch.cuda.is_available(), flush=True)\nprint("DRIVER_LIBRARIES_IN_THIS_PROCESS", flush=True)\nfor line in Path("/proc/self/maps").read_text().splitlines():\n    if any(value in line for value in ("libcuda.so", "libixthunk.so", "libixml.so")):\n        print(line.split()[-1], flush=True)\n'
```

## 20261104T141043Z-inspect-direct-install-prerequisites-5Kp1dx

退出码：`1`

```bash
bash -c set\ -e\;\ ls\ -ld\ /mnt/share/user_homes/zyp/models/Qwen/Qwen3-4B\ /models/Qwen3-4B\ /models/Qwen3.6-27B\ /models/Qwen3.6-35B-A3B\ 2\>/dev/null\ \|\|\ true\;\ ls\ -l\ /usr/local/bin/python\*\ /usr/local/bin/vllm\ /usr/local/bin/pip\*\ 2\>/dev/null\;\ ps\ -eo\ pid\,ppid\,etime\,args\ \|\ grep\ -E\ \"\[v\]llm.entrypoints.cli.main\|\[t\]ext_client.py\"\;\ cat\ /workspace/repro/src/vllm-plugin-FL/pyproject.toml\ \|\ head\ -n\ 75\;\ sed\ -n\ \"1\,130p\"\ /workspace/repro/src/vllm-plugin-FL/.github/scripts/install_flaggems_vllm.py
```

## 20261104T141120Z-snapshot-original-system-python-Bqs5as

退出码：`0`

```bash
env -u PYTHONPATH /usr/local/bin/python -c $'from importlib import metadata\nfrom pathlib import Path\nimport json\nimport os\nimport sys\nprint("python", sys.executable, sys.version)\nprint("PYTHONPATH", os.environ.get("PYTHONPATH"))\nfor name in ("vllm", "vllm-plugin-fl", "torch", "flagtree", "flag-gems", "flaggems-vllm", "numpy", "openai", "transformers", "tokenizers"):\n    try:\n        package = metadata.distribution(name)\n        print(name, package.version, package._path)\n    except metadata.PackageNotFoundError:\n        print(name, "NOT_INSTALLED")\nimport torch\nfor device in range(torch.cuda.device_count()):\n    free,total = torch.cuda.mem_get_info(device)\n    print("GPU",device,torch.cuda.get_device_name(device),round(free/2**30,3),round(total/2**30,3))\nprint("MODEL_PATH", Path("/mnt/share/user_homes/zyp/models/Qwen/Qwen3-4B").exists(), Path("/models/Qwen3-4B/config.json").is_file())\n'
```

## 20261104T141121Z-inspect-install-scripts-IoNV4X

退出码：`0`

```bash
bash -c head\ -n\ 75\ /workspace/repro/src/vllm-plugin-FL/pyproject.toml\;\ sed\ -n\ \"1\,135p\"\ /workspace/repro/src/vllm-plugin-FL/.github/scripts/install_flaggems_vllm.py\;\ grep\ -R\ -n\ \"ILUVATAR.\*TIMEOUT\\\|VLLM_ENGINE_ITERATION_TIMEOUT_S\\\|VLLM_RPC_TIMEOUT\"\ /workspace/repro/src/vllm-plugin-FL/vllm_fl\ \|\ head\ -n\ 20
```

## 20261104T141150Z-baseline-028-serve-direct-Z0CpPV

退出码：`1`

```bash
env -u PYTHONPATH -u VLLM_VENDOR PATH=/usr/local/bin:/usr/bin:/bin PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES=0\,1\,2\,3 COREX_VISIBLE_DEVICES=0\,1\,2\,3 GEMS_VENDOR=iluvatar VLLM_PLUGINS=fl USE_FLAGGEMS=1 VLLM_ENGINE_ITERATION_TIMEOUT_S=36000 VLLM_RPC_TIMEOUT=36000000 VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3600 /usr/local/bin/vllm serve /models/Qwen3-4B --served-model-name qwen --host 127.0.0.1 --enforce-eager --port 8060 --max-model-len 32768
```

## 20261104T141223Z-inspect-pr674-current-head-k72CJz

退出码：`0`

```bash
python3 -c $'import json\nimport urllib.request\nurl = "https://api.github.com/repos/flagos-ai/vllm-plugin-FL/pulls/674"\nwith urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"iluvatar-repro-doc-check"}), timeout=25) as response:\n    result = json.load(response)\nprint(json.dumps({key:result.get(key) for key in ("html_url","state","title","merged")},ensure_ascii=False))\nprint("HEAD",result["head"]["sha"],result["head"]["repo"]["full_name"],result["head"]["ref"])\nprint("BASE",result["base"]["ref"])\n'
```

## 20261104T141247Z-inspect-system-build-tools-tymyI1

退出码：`0`

```bash
env -u PYTHONPATH /usr/local/bin/python -c $'from importlib import metadata\nfor name in ("setuptools","setuptools-scm","setuptools-rust","scikit-build-core","pybind11","ninja","cmake","packaging","wheel","jinja2","sqlalchemy"):\n    try:\n        print(name,metadata.version(name))\n    except metadata.PackageNotFoundError:\n        print(name,"MISSING")\n'
```

## 20261104T141248Z-install-system-build-tools-efh7c7

退出码：`0`

```bash
env -u PYTHONPATH /usr/local/bin/python -m pip install --no-deps setuptools==80.10.2 setuptools-scm==10.2.1 setuptools-rust==1.13.0 scikit-build-core==0.11.0 pybind11==3.1.0 ninja==1.13.0 cmake==4.4.2 packaging==26.2 wheel
```

## 20261104T141303Z-baseline-028-curl-direct-RVUFFZ

退出码：`7`

```bash
curl --noproxy \* --fail-with-body --connect-timeout 5 --max-time 15 -sS http://127.0.0.1:8060/v1/chat/completions -H Content-Type:\ application/json -d \{\"model\":\"qwen\"\,\"messages\":\[\{\"role\":\"user\"\,\"content\":\"详细介绍下人工智能\"\}\]\,\"max_tokens\":256\,\"chat_template_kwargs\":\{\"enable_thinking\":false\}\}
```

## 20261104T141303Z-install-system-vllm032-editable-ndzMy1

退出码：`0`

```bash
env -u PYTHONPATH -u VLLM_VENDOR VLLM_TARGET_DEVICE=empty VLLM_VERSION_OVERRIDE=0.32.0 /usr/local/bin/python -m pip install -v --no-build-isolation --no-deps -e /workspace/repro/src/vllm
```

## 20261104T141352Z-install-system-plugin674-editable-EjZhJ7

退出码：`0`

```bash
env -u PYTHONPATH -u VLLM_VENDOR /usr/local/bin/python -m pip install --no-build-isolation --no-deps -e /workspace/repro/src/vllm-plugin-FL
```

## 20261104T141353Z-use-local-flaggems-source-th6Ub2

退出码：`0`

```bash
git config --file /workspace/repro/gitconfig url.file:///workspace/repro/src/FlagGems-vllm.insteadOf https://github.com/flagos-ai/FlagGems-vllm.git
```

## 20261104T141806Z-install-system-flaggems-vllm-txhzqA

退出码：`0`

```bash
env -u PYTHONPATH GIT_CONFIG_GLOBAL=/workspace/repro/gitconfig /usr/local/bin/python /workspace/repro/src/vllm-plugin-FL/.github/scripts/install_flaggems_vllm.py
```

## 20261104T141913Z-activate-direct-document-environment-5O4Sxn

退出码：`0`

```bash
cp /workspace/repro/direct-doc-checks/env-direct.sh /workspace/repro/env-direct.sh
```

## 20261104T141913Z-transfer-direct-document-snippets-PapoY3

退出码：`0`

```bash
tar -C /workspace/repro/direct-doc-checks -xf -
```

## 20261104T141913Z-verify-system032-direct-imports-jzY0Fm

退出码：`0`

```bash
python /workspace/repro/direct-doc-checks/inline-06.py
```

## 20261104T141941Z-recover-original-core-fingerprint-SPIhJh

退出码：`0`

```bash
python -c $'import json\nfrom pathlib import Path\nroot=Path("/workspace/repro")\nsource=next((root/"logs").glob("*-snapshot-original-system-python-*/output.log"))\nexpected={}\nfor line in source.read_text().splitlines():\n    values=line.split()\n    if len(values)>1 and values[0] in ("torch","flagtree","flag-gems","numpy"):\n        expected[values[0]]=values[1]\nassert len(expected)==4,expected\n(root/"logs/core-before-upgrade.json").write_text(json.dumps(expected,indent=2))\nprint("BASELINE_FINGERPRINT_FROM",source,expected)\n'
```

## 20261104T141941Z-verify-direct-document-runtime-aWZYSd

退出码：`0`

```bash
python /workspace/repro/direct-doc-checks/inline-05.py
```

## 20261104T141943Z-system032-4b-direct-serve-OvyW98

退出码：`0`

```bash
vllm serve /models/Qwen3-4B/ --served-model-name qwen --host 127.0.0.1 --enforce-eager --port 8060 --max-model-len 32768
```

## 20261104T142043Z-inspect-direct-4b-startup-e2dRY7

退出码：`7`

```bash
bash -c tail\ -n\ 32\ /workspace/repro/logs/\*system032-4b-direct-serve\*/output.log\;\ curl\ --noproxy\ \"\*\"\ --connect-timeout\ 3\ --max-time\ 5\ --fail-with-body\ -sS\ http://127.0.0.1:8060/v1/models
```

## 20261104T142131Z-system032-4b-direct-curl-lIGhyy

退出码：`0`

```bash
curl --noproxy \* --fail-with-body -sS --max-time 300 http://127.0.0.1:8060/v1/chat/completions -H Content-Type:\ application/json -d \{\"model\":\"qwen\"\,\"messages\":\[\{\"role\":\"user\"\,\"content\":\"详细介绍下人工智能\"\}\]\,\"max_tokens\":256\,\"chat_template_kwargs\":\{\"enable_thinking\":false\}\}
```

## 20261104T142131Z-system032-4b-direct-stream-fVYyzo

退出码：`2`

```bash
env NO_PROXY=127.0.0.1\,localhost no_proxy=127.0.0.1\,localhost python /workspace/repro/direct-doc-checks/inline-03.py
```

## 20261104T142145Z-system032-4b-direct-stream-retry-vzmoQu

退出码：`0`

```bash
env NO_PROXY=127.0.0.1\,localhost no_proxy=127.0.0.1\,localhost python /workspace/repro/direct-doc-checks/inline-03.py
```

## 20261104T142145Z-transfer-direct-stream-snippet-OcSV0S

退出码：`0`

```bash
tar -C /workspace/repro/direct-doc-checks -xf -
```

## 20261104T142310Z-stop-tested-system032-4b-server-VLlF4V

退出码：`0`

```bash
python3 -c $'import os\nfrom pathlib import Path\nimport signal\nimport time\nmodel="/models/Qwen3-4B"\nfound=[]\nfor directory in Path("/proc").iterdir():\n    if not directory.name.isdigit():\n        continue\n    try:\n        args=[part.decode(errors="replace") for part in (directory/"cmdline").read_bytes().split(b"\\x00") if part]\n        if any(arg.rstrip("/")==model for arg in args) and "--port" in args and args[args.index("--port")+1]=="8060" and any(Path(arg).name=="vllm" for arg in args[:2]):\n            found.append(int(directory.name))\n    except (FileNotFoundError,ProcessLookupError,PermissionError):\n        pass\nassert len(found)==1,found\nprint("Stopping only tested server",found[0],model,flush=True)\nos.kill(found[0],signal.SIGINT)\nfor attempt in range(20):\n    if not Path("/proc/"+str(found[0])).exists():\n        print("SERVER_STOPPED",flush=True)\n        break\n    time.sleep(1)\nelse:\n    raise SystemExit("Server still exiting; inspect before starting next model")\n'
```

## 20261104T142329Z-system032-large-text-precheck-I2xBM5

退出码：`0`

```bash
python /workspace/repro/direct-doc-checks/inline-06.py
```

## 20261104T142333Z-system032-27b-direct-serve-Oy5rqn

退出码：`0`

```bash
vllm serve /models/Qwen3.6-27B --served-model-name qwen --host 127.0.0.1 --port 8060 -tp 4 --dtype bfloat16 --language-model-only --enforce-eager --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 --gpu-memory-utilization 0.70
```

## 20261104T142410Z-inspect-direct-27b-startup-5IiMPl

退出码：`7`

```bash
bash -c tail\ -n\ 22\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log\ 2\>/dev/null\;\ curl\ --noproxy\ \"\*\"\ --connect-timeout\ 3\ --max-time\ 5\ --fail-with-body\ -sS\ http://127.0.0.1:8060/v1/models
```

## 20261104T142445Z-inspect-direct-27b-load-progress-8cNSsY

退出码：`0`

```bash
bash -c tail\ -n\ 18\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log\;\ ps\ -eo\ pid\,ppid\,etime\,stat\,args\ \|\ grep\ -E\ \"\[V\]LLM\|\[v\]llm\ serve\|\[m\]ultiprocessing.spawn\"\ \|\ head\ -n\ 12
```

## 20261104T142524Z-check-explicit-bash-system-python-iSOTy9

退出码：`0`

```bash
python3 -c $'import os\nfrom pathlib import Path\nimport subprocess\nroot=Path("/workspace/repro")\nlog=root/"logs/explicit-bash-session-check.log"\nresult=subprocess.run(["script","-q","-f","-c","bash --noprofile --norc -i",str(log)],input="set -o pipefail\\nsource /workspace/repro/env-direct.sh\\npython -c \'import sys; print(sys.executable); assert sys.prefix == sys.base_prefix\'\\necho EXPLICIT_BASH_AND_SYSTEM_PYTHON_PASS\\nexit\\n",text=True,capture_output=True,timeout=20)\nprint(result.stdout)\nprint(result.stderr)\nassert result.returncode==0,result.returncode\nassert "EXPLICIT_BASH_AND_SYSTEM_PYTHON_PASS" in result.stdout\nassert "Illegal option" not in result.stdout\nprint("SESSION_ENTRY_PASS")\n'
```

## 20261104T142524Z-system032-final-pip-fingerprint-a3tZXr

退出码：`0`

```bash
bash -c set\ -o\ pipefail\;\ env\ -u\ PYTHONPATH\ /usr/local/bin/python\ -m\ pip\ list\ --format=json\ \>\ \"\$REPRO_ROOT/logs/system032-packages.json\"\;\ env\ -u\ PYTHONPATH\ /usr/local/bin/python\ -m\ pip\ check\ \>\ \"\$REPRO_ROOT/logs/system032-pip-check.txt\"\ 2\>\&1\;\ status=\$\?\;\ printf\ \"%s\\n\"\ \"\$status\"\ \>\ \"\$REPRO_ROOT/logs/system032-pip-check-exit-code.txt\"\;\ cat\ \"\$REPRO_ROOT/logs/system032-pip-check.txt\"\;\ echo\ \"PIP_CHECK_EXIT_CODE=\$status\"
```

## 20261104T142614Z-inspect-direct-27b-ready-xdguBT

退出码：`7`

```bash
bash -c tail\ -n\ 16\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log\;\ curl\ --noproxy\ \"\*\"\ --connect-timeout\ 3\ --max-time\ 5\ --fail-with-body\ -sS\ http://127.0.0.1:8060/v1/models
```

## 20261104T142704Z-inspect-direct-27b-weight-progress-b5ZwHK

退出码：`0`

```bash
bash -c tail\ -n\ 12\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log
```

## 20261104T142735Z-inspect-direct-27b-warmup-h7WSWg

退出码：`0`

```bash
bash -c tail\ -n\ 14\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log
```

## 20261104T142753Z-system032-27b-direct-curl-RjYZEH

退出码：`0`

```bash
curl --noproxy \* --fail-with-body -sS --max-time 300 http://127.0.0.1:8060/v1/chat/completions -H Content-Type:\ application/json -d \{\"model\":\"qwen\"\,\"messages\":\[\{\"role\":\"user\"\,\"content\":\"详细介绍下人工智能\"\}\]\,\"max_tokens\":256\,\"chat_template_kwargs\":\{\"enable_thinking\":false\}\}
```

## 20261104T142847Z-inspect-direct-27b-first-request-gdJ4Vf

退出码：`0`

```bash
bash -c tail\ -n\ 12\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log
```

## 20261104T142925Z-inspect-direct-27b-request-progress-54lhc2

退出码：`0`

```bash
bash -c tail\ -n\ 5\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log
```

## 20261104T143025Z-inspect-direct-27b-generation-status-LMckeU

退出码：`0`

```bash
bash -c tail\ -n\ 4\ /workspace/repro/logs/\*system032-27b-direct-serve\*/output.log
```

## 20261104T143117Z-stop-tested-system032-27b-server-7EZr1u

退出码：`0`

```bash
python3 -c $'import os\nfrom pathlib import Path\nimport signal\nimport time\nmodel="/models/Qwen3.6-27B"\nfound=[]\nfor directory in Path("/proc").iterdir():\n    if not directory.name.isdigit():\n        continue\n    try:\n        args=[part.decode(errors="replace") for part in (directory/"cmdline").read_bytes().split(b"\\x00") if part]\n        if model in args and "--port" in args and args[args.index("--port")+1]=="8060" and any(Path(arg).name=="vllm" for arg in args[:2]):\n            found.append(int(directory.name))\n    except (FileNotFoundError,ProcessLookupError,PermissionError):\n        pass\nassert len(found)==1,found\nprint("Stopping only tested server",found[0],model,flush=True)\nos.kill(found[0],signal.SIGINT)\nfor attempt in range(30):\n    if not Path("/proc/"+str(found[0])).exists():\n        print("SERVER_STOPPED",flush=True)\n        break\n    time.sleep(1)\nelse:\n    raise SystemExit("Server still exiting; inspect before next model")\n'
```

## 20261104T143141Z-system032-35b-precheck-T2yoHf

退出码：`0`

```bash
python /workspace/repro/direct-doc-checks/inline-06.py
```

## 20261104T143145Z-system032-35b-direct-serve-y5yzkY

退出码：`0`

```bash
vllm serve /models/Qwen3.6-35B-A3B --served-model-name qwen --host 127.0.0.1 --port 8060 -tp 4 --dtype bfloat16 --language-model-only --enforce-eager --max-model-len 4096 --max-num-seqs 4 --max-num-batched-tokens 512 --gpu-memory-utilization 0.70
```

## 20261104T143219Z-inspect-direct-35b-startup-O6CH5j

退出码：`0`

```bash
bash -c tail\ -n\ 16\ /workspace/repro/logs/\*system032-35b-direct-serve\*/output.log\ 2\>/dev/null
```

## 20261104T143302Z-inspect-direct-35b-load-progress-jNfxAE

退出码：`0`

```bash
bash -c tail\ -n\ 12\ /workspace/repro/logs/\*system032-35b-direct-serve\*/output.log
```

## 20261104T143359Z-inspect-direct-35b-warmup-OrjEWO

退出码：`0`

```bash
bash -c tail\ -n\ 14\ /workspace/repro/logs/\*system032-35b-direct-serve\*/output.log
```

## 20261104T143415Z-system032-35b-direct-curl-h383A8

退出码：`0`

```bash
curl --noproxy \* --fail-with-body -sS --max-time 300 http://127.0.0.1:8060/v1/chat/completions -H Content-Type:\ application/json -d \{\"model\":\"qwen\"\,\"messages\":\[\{\"role\":\"user\"\,\"content\":\"详细介绍下人工智能\"\}\]\,\"max_tokens\":256\,\"chat_template_kwargs\":\{\"enable_thinking\":false\}\}
```

## 20261104T143511Z-inspect-direct-35b-request-progress-54mjLs

退出码：`0`

```bash
bash -c tail\ -n\ 8\ /workspace/repro/logs/\*system032-35b-direct-serve\*/output.log
```

## 20261104T143720Z-stop-tested-system032-35b-server-Es1RlW

退出码：`0`

```bash
python3 -c $'import os\nfrom pathlib import Path\nimport signal\nimport time\nmodel="/models/Qwen3.6-35B-A3B"\nfound=[]\nfor directory in Path("/proc").iterdir():\n    if not directory.name.isdigit():\n        continue\n    try:\n        args=[part.decode(errors="replace") for part in (directory/"cmdline").read_bytes().split(b"\\x00") if part]\n        if model in args and "--port" in args and args[args.index("--port")+1]=="8060" and any(Path(arg).name=="vllm" for arg in args[:2]):\n            found.append(int(directory.name))\n    except (FileNotFoundError,ProcessLookupError,PermissionError):\n        pass\nassert len(found)==1,found\nprint("Stopping only tested server",found[0],model,flush=True)\nos.kill(found[0],signal.SIGINT)\nfor attempt in range(30):\n    if not Path("/proc/"+str(found[0])).exists():\n        print("SERVER_STOPPED",flush=True)\n        break\n    time.sleep(1)\nelse:\n    raise SystemExit("Server still exiting; inspect resources")\n'
```

## 20261104T143741Z-final-system032-resources-RckKZs

退出码：`0`

```bash
python /workspace/repro/direct-doc-checks/inline-06.py
```

## 20261104T143746Z-final-system032-source-commits-8dpjMH

退出码：`0`

```bash
bash -c set\ -e\;\ git\ -C\ /workspace/repro/src/vllm\ rev-parse\ HEAD\;\ git\ -C\ /workspace/repro/src/vllm-plugin-FL\ rev-parse\ HEAD\;\ git\ -C\ /workspace/repro/src/vllm\ status\ --short\;\ git\ -C\ /workspace/repro/src/vllm-plugin-FL\ status\ --short\;\ sha256sum\ /models/Qwen3-4B/config.json\ /models/Qwen3.6-27B/config.json\ /models/Qwen3.6-35B-A3B/config.json
```
