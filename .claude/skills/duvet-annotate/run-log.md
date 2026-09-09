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
