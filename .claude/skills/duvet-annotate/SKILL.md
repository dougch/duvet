# Skill: duvet-annotate

Unsupervised loop that annotates aws-lc crypto source with duvet RFC citation comments.

## Invocation

```
/loop Unsupervised duvet annotation loop for aws-lc.

You are running an unsupervised annotation loop. Execute directly — do not re-delegate.

State file: /Users/dougch/gitrepos/aws-lc/.duvet/annotation-loop-progress.json
Source root: /Users/dougch/gitrepos/aws-lc
Report command: (cd /Users/dougch/gitrepos/aws-lc && duvet report --config-path .duvet/config.toml --json /tmp/duvet-report.json 2>/dev/null; python3 /Users/dougch/gitrepos/duvet/.claude/skills/duvet-annotate/check_duvet.py)

Each tick:
1. Read state file. Find the first requirement with status "pending".
2. If none, check if all committed RFCs are done. If so, stop the loop.
3. For the pending requirement, find the best matching function/code block in the source file listed in annotation_file (or search if null).
4. Insert a duvet citation block immediately before the function signature:
   //= <target_url>
   //# <quoted requirement text, one line per //# line>
5. Update the state file: set status to "annotated", annotation_file, annotation_line.
6. If all requirements for the current RFC are annotated or skipped: run duvet report, verify the requirements show as CITED, then commit with message: "feat(duvet): annotate <rfc-id> section-N MUSTs"
7. Update committed: true in state file.
8. Call ScheduleWakeup with delaySeconds: 60 and noop: false to continue, OR stop: true if all RFCs complete.

Rules:
- Scope: crypto/ only. Skip libssl/TLS.
- Appendix/theoretical requirements that are curve properties (not code behavior): set status "skip" with skip_reason.
- Never annotate test files.
- aws-lc is a public repo. Never commit SIM links, CoE numbers, or internal Amazon references.
- Annotation format is exactly two comment lines, no extra blank lines between them and the function.
```

## Annotation Format

```c
//= https://www.rfc-editor.org/rfc/rfcNNNN#section-N
//# Requirement text verbatim from the RFC, wrapped so each
//# line continues the quote on a new //# line.
static void target_function(...) {
```

## State File Schema

`/Users/dougch/gitrepos/aws-lc/.duvet/annotation-loop-progress.json`

```json
{
  "version": 1,
  "rfcs": [{
    "rfc": "rfc7748",
    "spec_url": "...",
    "committed": true,
    "requirements": [{
      "id": "rfc7748-s5-must1",
      "section": "section-5",
      "level": "MUST",
      "quote": "...",
      "target_url": "...",
      "status": "annotated|skip|pending",
      "annotation_file": "crypto/...",
      "annotation_line": 143,
      "skip_reason": null
    }]
  }]
}
```

## Selecting the Next RFC

See [rfc-candidates.md](rfc-candidates.md) for measured MUST counts, gate criteria, and the queue. Do not pick an RFC by raw MUST count — apply the gates:

1. **Body MUST count ≥ 1** — many algorithm RFCs extract to zero MUSTs (they specify by pseudocode).
2. **Appendix ratio < 25%** — high appendix share means ASN.1 encoding rules, not code behavior.
3. **Actor filter** — drop issuer/CA/sender-side MUSTs; aws-lc validates and computes, it does not issue.
4. **Code locality** — prefer a bounded file set (tiebreak).
5. **Satisfying code is inside `config.toml`'s source patterns** — as of
   `53f0f0955` the config covers all of `crypto/**` plus `include/openssl/*.h`,
   so this gate now only rejects code outside `crypto/` (notably `crypto/obj`
   and `crypto/asn1` are *in* scope, but `ssl/` is not). `grep` for the OID or
   structure name before queueing.

**Queue is empty** as of 2026-09-09. RFC 5280 (X.509) is the only remaining
candidate with volume and needs an actor-filter pass first — see
rfc-candidates.md.

### The two config axes are independent

`[[source]]` patterns control **where duvet looks for citations**.
`[[requirement]]` blocks alone determine the report's **requirement
denominator**. Widening sources cannot pull in new requirements — verified by
taking sources scanned from 294 to 586 and getting byte-identical CITED/UNCITED
counts. Adding an RFC to the report always means adding a `[[specification]]` +
`[[requirement]]` pair, never a source pattern.

### Two traps when adding an RFC

- **Config location matters.** Duvet resolves `[[requirement]]` and
  specification paths relative to the *config file's directory*. A config copied
  to `/tmp` fails with confusing `missing section` errors even with unchanged
  contents. Test configs must live in `.duvet/`.
- **`duvet extract` mirrors the source path beneath `-o`.** Output lands at
  `.duvet/requirements/.../rfcNNNN/.duvet/specifications/.../rfcNNNN/*.toml`.
  Flatten it with a recursive glob, not a hardcoded path, or you silently get
  zero requirements.

## Adding a New RFC

1. Download RFC text: `curl -s https://www.rfc-editor.org/rfc/rfcNNNN.txt -o /Users/dougch/gitrepos/aws-lc/.duvet/specifications/www.rfc-editor.org/rfc/rfcNNNN.txt`
2. Extract requirements: `(cd /Users/dougch/gitrepos/aws-lc && duvet extract .duvet/specifications/www.rfc-editor.org/rfc/rfcNNNN.txt -o .duvet/requirements/www.rfc-editor.org/rfc/rfcNNNN/)`
3. Add to `.duvet/config.toml`:
   ```toml
   [[specification]]
   source = "https://www.rfc-editor.org/rfc/rfcNNNN"
   format = "ietf"

   [[requirement]]
   pattern = ".duvet/requirements/www.rfc-editor.org/rfc/rfcNNNN/**/*.toml"
   ```
4. Add RFC entry to state file with all MUSTs as `status: "pending"`.

## Report Verification

`duvet report --require-citations` exits non-zero whenever any requirement is
uncited, which is the normal steady state here (intentional skips stay uncited
forever). Drop the flag and read [check_duvet.py](check_duvet.py) output
instead — compare CITED counts against the state file's `annotated` counts.

## Skip Categories

Seven, discovered in this order. Record one in `skip_reason`, and always say
*why* in enough detail that a reviewer can disagree with the call.

1. **Appendix / theoretical** — a property of the algorithm's definition, not of
   any code path (RFC 7748 appendix-A curve properties).
2. **Caller obligation** — the API cannot enforce it across calls (RFC 3610 and
   RFC 8439 nonce uniqueness).
3. **Out of source scope** — real code behavior, but the satisfying code sits
   outside `config.toml`'s source patterns. Mostly retired now that sources
   cover `crypto/**`; still applies to `ssl/`.
4. **Specification author** — addressed to future RFC authors, not to
   implementers ("Future specifications that define new KDFs MUST specify
   bounds", RFC 9180 §7.2.1). No implementation can satisfy it. This is a third
   actor beyond Gate 3's issuer/validator split.
5. **Not implemented** — the feature does not exist in aws-lc, so there is no
   code to cite (RFC 9180 PSK modes, NIST-curve KEMs). State the verified fact
   that establishes it, not an assumption.
6. **Design-level security property** — a property of the construction rather
   than of any code path.
7. **API permits the prohibited behavior** — the requirement forbids something
   and the API allows a caller to do it (RFC 8439 tag truncation via
   caller-selectable `tag_len`). Do **not** assert this as a defect; record the
   evidence and flag it for maintainer review. Often the requirement's actor is
   a protocol rather than the primitive, which is a legitimate defense.

Categories 4-7 all came from RFCs outside the FIPS module, which is why the
annotatable ratio fell from 67% to 41% once those were in scope.

## Run Log

See [run-log.md](run-log.md) for wall-clock and token stats per run.
