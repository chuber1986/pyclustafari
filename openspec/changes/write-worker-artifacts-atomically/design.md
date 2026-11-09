# Design

## Context

The worker (`workerstub.py`) writes `.state` (truncate-write), `.res` (`joblib.dump` onto the final path), and appends `.log` lines in place. The caller-side reader (`Runnable._read_job_file()`) treats any unreadable result file as "no result" → FAILED. Artifact dir is `~/.clustafari` on NFS-shared cluster home, so final-path readers race with in-place writes. All artifact files share the job-file stem in one per-run directory owned by a single worker, so temp-name collisions are not a concern.

## Goals / Non-Goals

**Goals:**
- Final paths of `.state`, `.res`, `.log` never expose partial content: temp file in the same directory + `os.replace()`.
- Corrupt-result tolerance in `_read_job_file()` logs a `logger.warning` when it triggers.

**Non-Goals:**
- No fsync/durability work (`os.replace` alone already fixes torn reads on the same filesystem; NFS close-to-open consistency gives the reader the renamed inode's content).
- No change to the file layout, state vocabulary, or reader tolerance semantics (tolerance stays as safety net).

## Decisions

- **Temp file in the same directory, then `os.replace`**: atomic on POSIX within one filesystem; rename is metadata-only over NFS. `.state`/`.log` temps use `with_suffix(".tmp")`; the result temp is the result path + `.tmp` suffix, so `.state.tmp` cannot collide with `.res.tmp`.
- **`set_state()`/`log()` write a whole snapshot and replace**: replaces truncate-write in place and append-in-place. For `.log` this keeps "message is in the log after `log()` returns" (each call rewrites the accumulated content); lines are few, so the rewrite cost is negligible.
- **Result dump: `joblib.dump(..., tmp_path)` then replace after it returns**: joblib accepts a path; the rename happens only after the dump is complete, so a crash mid-dump leaves the previous final path (or none) intact and a stray `.tmp`.
- **Warning in the reader tolerance**: `logger.warning("Result file %s unreadable (%s); treating as no result.", file, exc)` keeps the safety-net semantics visible (issue #14's honest-hardening clause).
- **Alternative rejected — write-final-then-fsync tricks or symlink swaps**: more moving parts, no atomicity gain over same-directory rename.

## Risks / Trade-offs

- [Extra renames per state transition (5–7 per run)] → negligible: tiny files, metadata-only ops.
- [Stray `.tmp` files after a mid-dump crash] → the dump helper unlinks its temp file on failure; anything left after a hard process kill is cleaned with the artifact directory by the existing cleanup and never read by the caller (reader only touches final paths).
- [NFS `os.replace` semantics] → rename within a directory is atomic on NFSv3/v4; this is the standard technique and strictly better than in-place truncate writes.

## Open Questions

None.
