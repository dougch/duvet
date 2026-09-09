# Duvet Annotation Loop — Run Log

Stats are context-window token deltas (cumulative context growth per turn), not raw Anthropic API input/output tokens.

---

## Run 1 — RFC 7748 (X25519/X448) Pilot

- **Date**: 2026-09-03
- **Model**: claude-sonnet-4-6
- **Commit**: `aa493fb57` — `feat(duvet): annotate RFC 7748 section-5 MUSTs`
- **Target file**: `crypto/fipsmodule/curve25519/curve25519_nohw.c`
- **Wall-clock**: 5 min 41 sec (loop invocation → commit)
- **Total context tokens consumed**: 16,125

### Per-Tick Breakdown

| Tick | Requirement | Function | Time | Tokens |
|------|-------------|----------|------|--------|
| 1 | MUST mask MSB in final byte (u-coord input) | `fe_frombytes` | ~1 min 27 sec | ~5,095 |
| 2 | MUST accept non-canonical values | `fe_frombytes_strict` | ~1 min | ~2,902 |
| 3 | MSB of output MUST be zero + report verify | `fe_tobytes` | ~2 min 17 sec | ~8,628 |
| — | Commit + loop stop | — | ~43 sec | ~202 |

### Outcomes

- 3 requirements annotated (section-5 implementation MUSTs)
- 3 requirements skipped (appendix-A theoretical curve properties — satisfied by curve definition, not addressable in code)
- 0 requirements failed / unmatched
- **Annotatable ratio: 50%** (3 of 6 MUSTs) — the calibration point for candidate gating

---

## Measurement Pass — RFC Candidate Survey

- **Date**: 2026-09-09
- **Model**: claude-sonnet-4-6
- **Scope**: 12 candidate RFCs from the Sept 3 `crypto/` grep, extracted and counted
- **Output**: [rfc-candidates.md](rfc-candidates.md)
- **Commits**: none (measurement ran in `/tmp`, repo untouched)

### Outcomes

- 5 RFCs rejected for having **zero MUSTs** (4493 CMAC, 3174 SHA-1, 5869 HKDF, 2898 PBKDF2, 7693 BLAKE2)
- 1 RFC rejected for **94% appendix/ASN.1 MUSTs** (8017 PKCS#1) — reversed an earlier ad-hoc recommendation
- Replaced a guessed `>5 MUST` gate with appendix-ratio + normative-density + actor gates
- Established the ceiling: **~18 annotatable body MUSTs** across all non-PKI algorithm RFCs
- Queue head set to **RFC 3610 (CCM)**

---

## Run 2 — RFC 3610 (CCM)

- **Date**: 2026-09-09
- **Model**: claude-sonnet-4-6
- **Commit**: `e9644ba09` — `feat(duvet): annotate RFC 3610 (CCM) section-2 MUSTs`
- **Target file**: `crypto/fipsmodule/cipher/e_aesccm.c` (single 730-line file)
- **Wall-clock**: 2 min 22 sec (21:06:21Z → 21:08:43Z)
- **Token delta**: not captured (loop ran without the per-tick instrumentation)

### Outcomes

- 8 requirements annotated across §2.2, §2.3, §2.5, §2.6 (5 edits — several
  edits carry two adjacent citations for the same code point)
- 2 requirements skipped, both the same reason: nonce-uniqueness is a caller
  obligation the AEAD/EVP API cannot enforce across calls
- 0 failed / mis-annotated
- **Annotatable ratio: 80%** (8 of 10 MUSTs) vs. RFC 7748's 50%

Confirms the gate criteria: RFC 3610 was the top pick on appendix-ratio (0%)
and code-locality, and it produced the highest ratio measured.

---

## Run 3 — Queue drain (3394 / 5649 / 3874 / 8032)

- **Date**: 2026-09-09
- **Model**: claude-sonnet-4-6
- **Commit**: `e1c68a53e` — `feat(duvet): annotate RFC 3394 section-5 MUST; close loop queue`

### Outcomes

| RFC | Result | Detail |
|------|--------|--------|
| 3394 | 1 annotated | §5 error-and-no-key-data at the `AES_unwrap_key` IV check |
| 5649 | 1 skip | §5 `AlgorithmIdentifier` params MUST be absent — ASN.1, out of source scope |
| 3874 | 1 skip | §4 OID requirement — lives in `crypto/obj`, out of source scope |
| 8032 | 2 already annotated | §5.1 and §8.7 cited in `curve25519.c` by the earlier example commit `08a21e09c` |

**New skip category discovered: out-of-source-scope.** Distinct from the
"appendix / theoretical" skips. An RFC can pass all four gates (body MUST,
0% appendix, right actor, bounded files) and still be unannotatable because
the code that satisfies it sits outside `config.toml`'s source patterns.
ASN.1/OID requirements are the recurring instance — they are real
implementation requirements, just not in `crypto/fipsmodule` or `crypto/evp`.

**Gate 5 to add**: check that the satisfying code is inside the configured
source patterns before queueing. Cheap — one `grep` for the OID or structure
name — and it would have kept 5649 and 3874 out of the queue.

### Cumulative

| | Annotated | Skipped | Total |
|---|---|---|---|
| RFC 7748 | 3 | 3 | 6 |
| RFC 3610 | 8 | 2 | 10 |
| RFC 3394 | 1 | 0 | 1 |
| RFC 5649 | 0 | 1 | 1 |
| RFC 3874 | 0 | 1 | 1 |
| RFC 8032 | 2 | 0 | 2 |
| **Total** | **14** | **7** | **21** |

Overall annotatable ratio: **67%** (14 of 21). Queue empty.

---

## Second Survey — RFCs outside `crypto/fipsmodule/`

- **Date**: 2026-09-09
- **Trigger**: the first survey's candidate list came from a grep of
  `crypto/fipsmodule/`, so it could only rediscover RFCs already in the
  configured source scope.
- **Output**: [rfc-candidates.md](rfc-candidates.md), "Second Survey" section
- **Commits**: `0e474b871` (removed dead `crypto/evp/**` source patterns, which
  matched zero files)

### Outcomes

- **79 RFCs** referenced only outside `crypto/fipsmodule/`. Two are algorithm
  RFCs that beat everything in the first survey: 9180 (HPKE, 37 body MUSTs) and
  8439 (ChaCha20-Poly1305, 8 body MUSTs).
- Ceiling revised **~18 → ~63** non-PKI body MUSTs. The earlier "does not scale
  by volume in crypto" conclusion was overstated — it holds for the FIPS module
  surface, not for aws-lc's algorithm code overall.
- **Verified that the two config axes are independent.** Widening `[[source]]`
  from `crypto/fipsmodule/**` to `crypto/**` took sources scanned from 294 to
  586 and left CITED/UNCITED **byte-identical** at 16/26. The report's
  requirement denominator comes only from `[[requirement]]` blocks; source
  patterns control where duvet looks for citations, nothing more.

Two measurement errors worth recording, both caught and corrected:

1. A first attempt concluded "widening sources breaks the report" from 4
   `missing section` errors. Cause was the **test config's location**, not its
   contents — duvet resolves `[[requirement]]` and specification paths relative
   to the config file's directory, so a config copied to `/tmp` fails even
   unchanged. A control run with an unchanged config in `/tmp` reproduced the
   same failure, which falsified the conclusion.
2. The candidate measurement pass returned zero MUSTs for all 6 RFCs.
   `duvet extract` mirrors the **source** path beneath `-o`, so output landed at
   `reqs/rfcN/specs/rfcN/*.toml` while the flattener searched for a path
   containing `specifications`. Any flattener that hardcodes one output path
   silently yields zero results.

---

## Run 4 — RFC 9180 (HPKE)

- **Date**: 2026-09-09
- **Commit**: `53f0f0955` — `feat(duvet): drop FIPS-only source scoping; annotate RFC 9180 (HPKE)`
- **Target file**: `crypto/hpke/hpke.c` (single 792-line file)
- **Scope decision**: dropped FIPS-approved-algorithm scoping from
  `config.toml`. HPKE is not FIPS-approved; including it makes the config track
  normative RFC requirements wherever they are implemented in `crypto/`.

### Outcomes

- 10 annotated across §4, §4.1, §5.1, §5.2, §7.1.4 via 6 edits
- 27 skipped — the largest skip set so far, and the reason the skip taxonomy
  grew from 3 categories to 6
- **Annotatable ratio: 27%** (10 of 37) — lowest measured, because §9
  (Security Considerations) is 12 MUSTs of caller obligations and design-level
  properties
- Report total CITED 16 → 26. HPKE is now the largest cited spec on the report.
- `gcc -fsyntax-only -Iinclude -Icrypto -I.` passes. The editor's clang
  diagnostics for this file are false positives — it lints without include
  paths, so one missing top-level header cascades into dozens of
  `Unknown type name` errors.

### New skip categories from this run

- **Specification author** — 7 MUSTs address future RFC authors ("Future
  specifications that define new KDFs MUST specify bounds"). No implementation
  can satisfy them. Gate 3 previously distinguished only issuer vs. validator.
- **Not implemented** — 5 PSK-mode MUSTs and 4 NIST-curve KEM MUSTs. Verified
  facts about aws-lc, not properties of the RFC: the only KEM is
  `EVP_HPKE_DHKEM_X25519_HKDF_SHA256` (zero P-256 references), the only modes
  are `HPKE_MODE_BASE` and `HPKE_MODE_AUTH`, and `psk`/`psk_id` are always
  passed `NULL, 0`.
- **Design-level security property** — 3 MUSTs stating properties of the
  construction rather than of any code path.

One skip flagged for maintainer review: aws-lc clamps the X25519 scalar inside
the scalar multiplication rather than at serialize/deserialize, and
`X25519_keypair` deliberately inverts the masking to detect non-conforming
peers. Not cited because the literal serialize/deserialize clamping the RFC
requires is not where aws-lc performs it.

---

## Run 5 — RFC 8439 (ChaCha20-Poly1305)

- **Date**: 2026-09-09
- **Commit**: `da0727fd5` — `feat(duvet): wire RFC 8439 (ChaCha20-Poly1305) into coverage`
- **Target files**: `crypto/cipher_extra/e_chacha20poly1305.c`,
  `crypto/poly1305/poly1305.c`

### Outcomes

- 3 annotated of 8 body MUSTs (**37%**):
  - §2.5 `r` clamping — `CRYPTO_poly1305_init`. The radix-2^26 masks
    (`0x3ffff03`, `0x3ffc0ff`, `0x3f03fff`, `0x00fffff`) fold the RFC's clamp
    into the limb split rather than doing it as a separate step.
  - §4 Poly1305 key unpredictability — `calc_tag`, where the one-time key is
    ChaCha20 keystream block 0.
  - §4 constant-time comparison — `CRYPTO_memcmp` in
    `chacha20_poly1305_open_gather`.
- 5 not cited: 2 caller obligations + 1 specification-author (state-file skips),
  and 2 tag-truncation MUSTs annotated `type=exception` (see follow-up below)
- Report total CITED 26 → 29
- `gcc -fsyntax-only` passes on both edited files

### Seventh skip category: API permits the prohibited behavior

RFC 8439 §4 says "any protocol using this algorithm MUST include the complete
tag" and "Tag truncation MUST NOT be done." aws-lc's
`aead_chacha20_poly1305_init` accepts any `tag_len` in 1..`POLY1305_TAG_LEN`,
and the `EVP_CIPHER` path accepts `EVP_CTRL_AEAD_SET_TAG` with any `arg` in the
same range — so a caller can request a truncated tag.

This is structurally different from the six earlier categories. The code does
not fail to implement something; it permits something the RFC forbids. Second
instance of this shape after the `AES_unwrap_key` observation from Run 3.

### Follow-up: `type=exception`, and the provenance check that decided it

Two corrections came out of reviewing this finding.

**1. A state-file `skip` is invisible in the report.** Those two MUSTs rendered
as plain `incomplete` — indistinguishable from requirements nobody examined. The
`skip_reason` was only ever in `annotation-loop-progress.json`, which duvet does
not read.

They were first annotated `//= type=TODO` on the reasoning that `report/ci.rs`
marks exceptions as fully covered, so `exception` declares the deviation
accepted — a maintainer's call. That was reversed once the provenance evidence
below was in hand, and the reversal was the right one: TODO carries **no** text
into the report (`reason=` is rejected on TODO by `comment/parser.rs`), so
choosing it meant the four pieces of evidence stayed in a `//` comment duvet
ignores. `type=exception` + `reason=` puts the justification in the report
verbatim, which is the whole point of recording it. Both are now:

```c
//= https://www.rfc-editor.org/rfc/rfc8439#section-4
//= type=exception
//= reason=Only an upper bound is enforced, so a caller may select a
//= reason=truncated tag. Inherited and intentional rather than an aws-lc
//= reason=divergence: ...
```

Multiple `//= reason=` lines are supported and joined with a single space.

**The lesson is about ordering, not about which type is correct.** The type
should be picked *after* the provenance check, not before — the evidence is what
distinguishes an accepted deviation from an unresolved gap, and it is also the
`reason=` text. Deciding first and investigating second produced the wrong
annotation and hid the investigation.

`check_duvet.py` was collapsing both `exception` and `todo` into UNCITED, hiding
exactly the requirements a reviewer needs. Now reports four columns:
CITED / TODO / EXCPT / UNCITED — rfc8439 reads 3 / 0 / 2 / 3.

**2. Checking fork provenance answered the question without a co-worker.** The
plan was to ask a teammate whether caller-selected `tag_len` is an accepted
deviation. Four commands made that unnecessary:

- `git log -S"tag_len > POLY1305_TAG_LEN"` → introduced by `de0b20268`,
  "ChaCha20-Poly1305 support.", Adam Langley, **2014-06-20**
- that date **predates RFC 8439** (2018) and RFC 7539 (2015) — the code predates
  the requirement it appears to violate
- current upstream BoringSSL (`crypto/cipher/e_chacha20poly1305.cc`, master) has
  the **identical** upper-bound-only check, 11 years later
- `include/openssl/aead.h` documents it as intended for *every* AEAD:
  "Authentication tags may be truncated by passing a size as |tag_len|"

So this is not an aws-lc divergence and not an oversight — it is a documented
property of the `EVP_AEAD` abstraction, inherited unchanged. The RFC's own
wording ("any protocol *using* this algorithm") addresses protocols, and aws-lc
ships the primitive. That is what justifies `type=exception`: an accepted,
documented deviation, with the evidence attached.

**Generalized into a rule** (see SKILL.md): before escalating an "API permits
what the spec forbids" finding to a human, establish provenance. Documented
intent plus unchanged upstream history is a stronger answer than a maintainer's
recollection, and cheaper for everyone. In a fork, the upstream history is
already in the repo.

### Cumulative after Run 5

| | Annotated | Skipped | Total |
|---|---|---|---|
| First four runs (7748 / 3610 / 3394 / 5649 / 3874 / 8032) | 14 | 7 | 21 |
| RFC 9180 | 10 | 27 | 37 |
| RFC 8439 | 3 | 5 | 8 |
| **Total** | **27** | **39** | **66** |

Overall annotatable ratio: **41%** (27 of 66), down from 67% before the two
non-FIPS RFCs. The drop is the finding, not a regression: the newly reachable
RFCs are larger and carry proportionally more caller-obligation and
specification-author requirements.
