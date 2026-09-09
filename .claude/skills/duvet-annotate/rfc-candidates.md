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
zero annotations, because the config then scoped sources to the
FIPS-approved-algorithm surface while the satisfying ASN.1/OID code lives in
`crypto/obj` and `crypto/asn1`.

**Largely retired as of `53f0f0955`.** Sources now cover all of `crypto/**` plus
`include/openssl/*.h`, so the gate only rejects code outside `crypto/` — chiefly
`ssl/`. Still worth one `grep` before queueing.

**Correction to the original wording.** This section previously said widening
`config.toml` would make such requirements annotatable "at the cost of enlarging
the report denominator." The cost claim was wrong. Source patterns and the
requirement denominator are independent axes: widening sources from
`crypto/fipsmodule/**` to `crypto/**` took sources scanned from 294 to 586 and
left CITED/UNCITED byte-identical at 16/26. The denominator grows only when a
`[[specification]]` + `[[requirement]]` pair is added. Widening sources is
therefore close to free.

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

### Second-survey RFCs, resolved 2026-09-09

| RFC | Result | Commit |
|---|---|---|
| 9180 | 10 annotated / 27 skip | `53f0f0955` |
| 8439 | 3 annotated / 5 skip | `da0727fd5` |

Both required dropping the FIPS-approved-algorithm scoping from
`config.toml`, done in `53f0f0955`.

### Remaining options, none queued

- **RFC 8452 (AES-GCM-SIV)** — 2 clean body MUSTs in
  `crypto/cipher_extra/e_aesgcmsiv.c`, now inside the source patterns, so Gate 5
  no longer blocks it. Its half-configured spec text (untracked in
  `.duvet/specifications/`, auto-discovered by `duvet report` as 4 phantom
  uncited requirements) was **deleted** 2026-09-09 rather than wired in. Re-add
  properly with a `[[specification]]` + `[[requirement]]` pair if wanted.
- **RFC 3962 (Kerberos AES)** — 2 body MUSTs, 0% appendix, in
  `crypto/cipher_extra/`. Now reachable. Low value and Kerberos-specific.
- **RFC 5280 (X.509)** — only after an actor-filter pass. Sole source of volume.

## Second Survey — RFCs Referenced Outside `crypto/fipsmodule/`

Measurement run: 2026-09-09. The first survey drew its candidate list from a
grep of `crypto/fipsmodule/`, which silently limited it to the configured source
scope. Re-grepping all of `crypto/` and `include/` found **79 RFCs referenced
only outside `crypto/fipsmodule/`**. Most are TLS-surface (out of scope) or
PKI/ASN.1 (deferred), but two are algorithm RFCs that beat everything in the
first survey:

| RFC | Algorithm | MUST | body | apdx % | Impl locality | Gate |
|---|---|---|---|---|---|---|
| 9180 | HPKE | **37** | 37 | 0% | `crypto/hpke/hpke.c` (792 L, 1 file) | **DONE** — 10/27, `53f0f0955` |
| 8439 | ChaCha20-Poly1305 | 8 | 8 | 0% | `crypto/cipher_extra/e_chacha20poly1305.c` (730 L) + `crypto/poly1305/poly1305.c` (299 L) | **DONE** — 3/5, `da0727fd5` |
| 7914 | scrypt | 0 | 0 | — | `crypto/evp_extra/` | REJECT — Gate 1 |
| 3962 | Kerberos AES | 2 | 2 | 0% | `crypto/cipher_extra/` | Low value, Kerberos-specific |
| 8009 | Kerberos AES-SHA2 | 0 | 0 | — | `crypto/cipher_extra/` | REJECT — Gate 1 |
| 3526 | MODP DH groups | 0 | 0 | — | `crypto/dh_extra/` | REJECT — Gate 1 |

**RFC 9180 alone has twice the body-MUST count of the entire first survey's
non-PKI total.** It is a single 792-line file with 0% appendix ratio — the best
locality/density combination measured. Its Gate 5 blocker is different in kind
from the ASN.1 cases: HPKE is not a FIPS-approved algorithm, so including it
contradicts the config's stated purpose rather than merely extending it.

### Actor breakdown of RFC 9180's 37 MUSTs (sampled, not fully classified)

- **§5.x (11)** — HPKE API: role separation (sender context MUST NOT decrypt),
  psk/psk_id pairing, sequence-number overflow. Most annotatable.
- **§7.x (11)** — KEM validation: all-zero X25519 DH output must abort, partial
  public-key validation for P-256/384/521, point-at-infinity rejection.
  Mostly annotatable and high-consequence.
- **§9.x (12)** — Security Considerations, mostly **not** annotatable: caller
  obligations ("Applications … MUST enforce the ordering property", "ikm MUST
  NOT be reused elsewhere").
- **§4.x (3)** — labeled KDF construction; partly annotatable.

**New actor category found: specification author.** Several MUSTs address future
RFC authors, not implementers — "Future specifications that define new KDFs MUST
specify bounds for these variable-length parameters" (§7.2.1), "Future KEM
instantiations MUST ensure …" (§9.6). Gate 3 previously only distinguished
issuer vs. validator; this is a third actor that no implementation can satisfy.

Rough annotatable estimate was **12–18 of 37**. The real pass produced **10**
(`53f0f0955`), so the estimate was 20–80% high. The §7.x block was the
overestimate: its NIST-curve public-key-validation MUSTs are unannotatable
because aws-lc implements only `EVP_HPKE_DHKEM_X25519_HKDF_SHA256` — a fact
about the implementation that no amount of reading the RFC would reveal.
**Sampling section headers predicts requirement counts; it does not predict
annotatability.**

### Method note

The first survey's candidate list was scoped by a grep of the already-configured
source tree, so it could only rediscover RFCs already in scope. Any future
survey must grep the **whole repo**, then apply Gate 5, rather than grepping
inside the configured scope and inheriting its blind spot.

## Ceiling

**Revised 2026-09-09 after the second survey.** The original figure was ~18
annotatable body MUSTs across all non-PKI algorithm RFCs, which was wrong
because the candidate list came from a grep confined to the configured source
scope. Adding RFCs 9180 and 8439 raises the non-PKI body-MUST total from ~18 to
**~63** (18 + 37 + 8), of which perhaps 30–40 are plausibly annotatable.

**Both additions are now done** (`53f0f0955`, `da0727fd5`), so the ceiling is no
longer a prediction — it is measured:

- **Inside the old FIPS-approved-algorithm scope: ~18, spent.** 14 annotated,
  7 skipped.
- **Non-FIPS algorithm code added 45 body MUSTs and yielded 13 annotations**
  (10 HPKE + 3 ChaCha20-Poly1305), not the 30–40 estimated. The scope decision
  roughly doubled the annotation count (14 → 27) and tripled the requirement
  count (21 → 66).
- **RFC 5280 (X.509)** remains the only path to three-digit numbers, and roughly
  16% of its body MUSTs are issuer-side (floor estimate from a keyword pass;
  188 of 261 were unclassified, so the real out-of-scope share is higher).

The "does not scale by volume in crypto" conclusion was overstated — it holds
for the FIPS module surface, not for aws-lc's algorithm code overall. But the
corrected version is more nuanced than "widen scope and get 3× the coverage":
**the requirement count scaled 3×; the annotation count scaled 2×; the
annotatable ratio fell from 67% to 41%.** Larger, more modern RFCs carry
proportionally more caller-obligation and specification-author requirements,
which are exactly the ones no implementation can cite.

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
