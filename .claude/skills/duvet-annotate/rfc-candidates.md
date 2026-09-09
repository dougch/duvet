# RFC Candidate Selection — Measured Data & Gate Criteria

Measurement run: 2026-09-09. All numbers from `duvet extract` over RFC text fetched from rfc-editor.org, counted by `level = "MUST"` in the emitted TOMLs. Note `duvet extract` maps RFC 2119 `SHALL` and `REQUIRED` to level `MUST`.

## Gate Criteria

Applied in order. No raw-MUST-count floor — an early `>5` threshold was a guess and the data contradicted it (it admitted RFC 8017, whose count is 94% noise, and excluded RFC 8452/3394/5649, which are small but clean).

**Gate 1 — Normative density: body MUST count ≥ 1.**
Many algorithm RFCs specify by pseudocode and test vectors, not normative statements, and extract to zero MUSTs. Nothing to annotate. Rejects: 4493, 3174, 5869, 2898, 7693.

**Gate 2 — Appendix ratio < 25%.**
The cheap discriminator, computable at extract time without reading any requirement. High appendix share means the MUSTs are ASN.1 encoding rules or module comments, not code behavior. Rejects: 8017 (94% appendix).

**Gate 3 — Actor filter.**
RFC MUSTs address distinct actors: issuer/CA/sender vs. validator/receiver/implementation. aws-lc is a library that validates and computes; it does not issue certificates. Issuer-side MUSTs are structurally unmatchable. Only material for PKI RFCs so far, but must be applied before committing to one.

**Gate 4 — Code locality (tiebreak, not a reject).**
Bounded file set beats sprawl. One file is ideal; a whole subdirectory means more ticks per requirement and more chances to misplace a citation.

**Gate 5 — Satisfying code is inside the configured source patterns.**
Added 2026-09-09 after RFC 5649 and RFC 3874 passed Gates 1–4 and then produced
zero annotations. `config.toml` scopes sources to `crypto/fipsmodule/**`,
`crypto/evp/**`, and `include/openssl/evp.h` — the FIPS-approved-algorithm
surface. ASN.1 `AlgorithmIdentifier` and OID requirements are satisfied in
`crypto/obj` and `crypto/asn1`, so they are real implementation requirements
that this config cannot cite. Check with one `grep` for the OID or structure
name before queueing.

This is a distinct skip category from "appendix / theoretical": the requirement
is about code behavior, the code exists, it is just outside the configured
scope. Widening `config.toml` would make them annotatable at the cost of
enlarging the report denominator.

## Measured Candidates

| RFC | Algorithm | MUST total | body | apdx | apdx % | Gate | Impl locality |
|---|---|---|---|---|---|---|---|
| 3610 | CCM mode | 10 | 10 | 0 | 0% | **PASS** | `crypto/fipsmodule/cipher/e_aesccm.c` (730 L, 1 file) |
| 8452 | AES-GCM-SIV | 2 | 2 | 0 | 0% | **PASS** | — |
| 8032 | EdDSA | 2 | 2 | 0 | 0% | **PASS** (in config) | `crypto/fipsmodule/curve25519/` |
| 7748 | X25519/X448 | 6 | 3 | 3 | 50% | **DONE** | `crypto/fipsmodule/curve25519/curve25519_nohw.c` |
| 3394 | AES Key Wrap | 1 | 1 | 0 | 0% | **PASS** | — |
| 5649 | Key Wrap + Pad | 1 | 1 | 0 | 0% | **PASS** | — |
| 3874 | SHA-224 | 1 | 1 | 0 | 0% | **PASS** | — |
| 5280 | X.509 | 279 | 261 | 18 | 6% | **DEFER** — needs Gate 3 | `crypto/x509/` (70 files, 18,050 L) |
| 8017 | PKCS#1 RSA | 32 | 2 | 30 | 94% | **REJECT** — Gate 2 | `crypto/fipsmodule/rsa/` + `crypto/rsa_extra/` (8 files, 4,716 L) |
| 4493 | AES-CMAC | 0 | 0 | 0 | — | **REJECT** — Gate 1 | — |
| 3174 | SHA-1 | 0 | 0 | 0 | — | **REJECT** — Gate 1 | — |
| 5869 | HKDF | 0 (2 SHOULD) | 0 | 0 | — | **REJECT** — Gate 1 | — |
| 2898 | PBKDF2 | 0 (7 MAY) | 0 | 0 | — | **REJECT** — Gate 1 | — |
| 7693 | BLAKE2 | 0 (2 SHOULD) | 0 | 0 | — | **REJECT** — Gate 1 | — |

Superseding pairs deduped before measurement: 3394/5649 (key wrap), 2898/6070 (PBKDF2), 3174/3874 (SHA).

## Queue

**Empty as of 2026-09-09.** All queued RFCs resolved:

| RFC | Result | Commit |
|---|---|---|
| 7748 | 3 annotated / 3 skip (appendix) | `aa493fb57` |
| 3610 | 8 annotated / 2 skip (caller obligation) | `e9644ba09` |
| 3394 | 1 annotated | `e1c68a53e` |
| 5649 | 1 skip (Gate 5 — ASN.1, out of scope) | `e1c68a53e` |
| 3874 | 1 skip (Gate 5 — OID, out of scope) | `e1c68a53e` |
| 8032 | 2 already annotated | `08a21e09c` (pre-existing) |

Actual annotated total: **14**, against a predicted ceiling of ~18. Gate 5
accounts for most of the gap.

### Remaining options, none queued

- **RFC 8452 (AES-GCM-SIV)** — 2 clean body MUSTs, but the implementation is
  `crypto/cipher_extra/e_aesgcmsiv.c`, outside the configured source patterns.
  Same Gate 5 problem as 5649/3874, resolvable only by widening scope. Its spec
  text is currently sitting in `.duvet/specifications/` untracked and is being
  auto-discovered by `duvet report` (4 uncited requirements) — remove it or wire
  it in properly; do not leave it half-configured.
- **RFC 5280 (X.509)** — only after an actor-filter pass. Sole source of volume.

## Ceiling

Total annotatable body MUSTs across all non-PKI algorithm RFCs in aws-lc: **~18**. This approach does not scale by volume in crypto. The value is per-requirement consequence, not coverage percentage. RFC 5280 is the only path to large numbers, and roughly 16% of its body MUSTs are issuer-side (floor estimate from a keyword pass; 188 of 261 were unclassified, so the real out-of-scope share is higher).

## Notes on RFC 8017

Worth recording because it is the clearest instance of the failure mode Gate 2 exists to catch. `appendix-C` extracts ASN.1 *module comments* as requirements:

```
-- the parameters MUST be present and MUST be NULL.
Version ::= INTEGER { two-prime(0), multi(1) } (CONSTRAINED BY {-- version MUST be multi if otherPrimeInfos present --})
```

These are not requirements on aws-lc's behavior; they are annotations inside an ASN.1 definition. The two body MUSTs are policy statements ("RSASSA-PSS is REQUIRED in new applications"), also not annotatable.

## Reproducing

```bash
mkdir -p /tmp/rfc-measure/specs /tmp/rfc-measure/reqs
cd /tmp/rfc-measure/specs
for n in 3610 8452 3394 5649 3874 5280 8017; do
  curl -sf "https://www.rfc-editor.org/rfc/rfc$n.txt" -o rfc$n.txt
done
cd /tmp/rfc-measure
for n in 3610 8452 3394 5649 3874 5280 8017; do
  duvet extract specs/rfc$n.txt -o reqs/rfc$n/
done
# then count level = "MUST" per file, splitting appendix-*.toml from the rest
```
