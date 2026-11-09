# Tasks

## 1. Implement

- [x] 1.1 Add `SubprocessInformation(RunInformation)` in `src/clustafari/runner/subprocess/info.py` holding the `Popen` handle, with `terminated()` override (`poll() is not None`)
- [x] 1.2 Wire `SubprocessRunner._run()` to construct `SubprocessInformation` from the spawned process and assign it to `runobj.info`; include the exit code in the termination failure message
- [x] 1.3 Add tests: dead worker (exits without writing state) → `get(blocking=True, timeout=...)` raises `StateError` promptly with stderr and exit code; healthy worker unaffected

## 2. Validate

- [x] 2.1 Run `openspec validate detect-dead-subprocess-worker` and fix any reported issues

## 3. Land

- [x] 3.1 Full lint + test suite green; commit
