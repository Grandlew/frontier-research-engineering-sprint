# Day 1 Reproducibility Report

## Experiment

**Repository:** `frontier-research-engineering-sprint`  
**Experiment:** Deterministic majority-label baseline harness  
**Dataset identifier:** `day01-toy-v1`  
**Seed:** `1729`  
**Initial Day 1 commit:** `40bd1e9`  
**Execution date:** 26 August 2026

## Objective

Establish a research-engineering harness in which repeated executions with identical scientific inputs produce byte-identical scientific results, even when operational fields such as run name, output directory and creation time differ.

The pre-fixed local reproducibility criterion was:

```text
SHA256(result_run_a) = SHA256(result_run_b) = SHA256(result_run_c)
```

The experiment also required a negative control demonstrating that volatile metadata inside the scientific result causes the reproducibility test to fail.

## Environment

The run manifest recorded:

```text
Operating system: Windows-11-10.0.26200-SP0
Python implementation: CPython
Python version: 3.12.0
Python build: tags/v3.12.0:0fb18b0, Oct 2 2023, 13:03:39
Compiler: MSC v.1935 64 bit (AMD64)
pytest: 9.0.1
```

The complete Python version string and platform identifier remain preserved in `manifest.json`.

## Reproducibility boundary

The scientific result contains only information capable of affecting or describing the scientific outcome:

- seed;
- dataset version;
- configuration fingerprint;
- baseline identity and learned label;
- ordered raw predictions;
- exact-match metric.

Operational metadata is written separately to `manifest.json`:

- run name;
- output directory;
- creation timestamp;
- Python and platform information;
- result filename and result hash.

This separation prevents operational changes from altering the scientific result digest.

## Commands

The package and test suite were executed from the repository root:

```powershell
python -m pytest -q

python scripts/run_day01.py --config configs/day01.json --output-dir artifacts/day01/run_a --run-name run_a
python scripts/run_day01.py --config configs/day01.json --output-dir artifacts/day01/run_b --run-name run_b
python scripts/run_day01.py --config configs/day01.json --output-dir artifacts/day01/run_c --run-name run_c
```

The output files were independently hashed with PowerShell:

```powershell
$h1 = (Get-FileHash artifacts/day01/run_a/result.json -Algorithm SHA256).Hash
$h2 = (Get-FileHash artifacts/day01/run_b/result.json -Algorithm SHA256).Hash
$h3 = (Get-FileHash artifacts/day01/run_c/result.json -Algorithm SHA256).Hash
($h1 -eq $h2) -and ($h2 -eq $h3)
```

## Positive-control results

All three independent runs produced the same digest:

```text
c1aef309395d62dea2bfddd3e508523577516205b760adf8879f80ef09614c9d
```

The independent PowerShell comparison returned:

```text
True
```

The configuration fingerprint was:

```text
7fb75395671ec52ae7faa1565bb2af83d458360850cb40256350bf9a53f46a69
```

The baseline learned label `"2"` from the training split only. Test predictions were deterministically ordered by `example_id`:

| Example | Target | Prediction | Correct |
|---|---:|---:|---|
| `e1` | `2` | `2` | Yes |
| `e2` | `8` | `2` | No |

The resulting exact-match score was:

```text
0.5
```

The complete test suite passed before the negative control:

```text
3 passed
```

## Deliberate failure: volatile timestamp contamination

The following field was temporarily injected into the scientific payload before serialization:

```python
scientific_payload["generated_at"] = datetime.now(UTC).isoformat()
```

The two executions retained the same aggregate metric, `exact_match=0.5`, but produced different hashes:

```text
eecce2068d323fe898b861d13733babab5b81809234762d99ede2fe4d0e3aa49
8a354cfdc63d7decc3c2e41ab2c74b3c9b0983d68da2994491bbfb34d70c445a
```

The reproducibility test failed at:

```python
assert first_hash == second_hash
```

This negative control demonstrates that equal aggregate metrics do not prove identical experimental artifacts. It also demonstrates that the test suite detects volatile metadata contaminating the scientific result.

## Restoration

The injected timestamp was removed. The committed implementation was restored, and the complete test suite passed again:

```text
3 passed
```

Git then reported:

```text
nothing to commit, working tree clean
```

The deliberate defect was never committed.

## Acceptance assessment

| Requirement | Evidence | Status |
|---|---|---|
| Typed immutable experiment configuration | Frozen, slotted dataclass | Passed |
| Invalid seed rejection | Test covers negative, Boolean and upper-bound seeds | Passed |
| Scientific/operational separation | Fingerprint and result exclude run metadata | Passed |
| Leakage-safe fitting | Majority label uses the training split only | Passed |
| Deterministic prediction order | Raw predictions ordered `e1`, `e2` | Passed |
| Canonical result serialization | Sorted compact JSON with UTF-8 and one newline | Passed |
| Exact-byte hashing | SHA-256 computed over bytes written to `result.json` | Passed |
| Repeated-run reproducibility | Three matching hashes | Passed |
| Negative-control sensitivity | Timestamp injection caused unequal hashes and test failure | Passed |
| Restoration | Full test suite passed and working tree became clean | Passed |

## Limitations

1. This establishes local determinism on one Windows/CPython environment, not cross-platform reproducibility.
2. Only Python's standard `random` generator is currently seeded. NumPy, PyTorch, CUDA, data-loader workers and distributed ranks are not yet involved.
3. The dataset identity is a declared version string, not a cryptographic digest of dataset contents.
4. The baseline and dataset are deliberately small; the result does not establish model quality or external validity.
5. The current tests validate the Day 1 contracts but are not exhaustive property-based or concurrency tests.
6. The manifest records the runtime environment but does not yet capture the Git commit, dependency lockfile or complete package inventory automatically.
7. Bitwise equality across future GPU hardware and kernels may be unavailable; later experiments may require pre-declared numerical tolerances and statistical equivalence instead.

## Conclusion

The Day 1 harness satisfies its local reproducibility contract. Scientifically identical runs produced byte-identical result files, while a deliberate violation of the scientific/operational boundary was detected. This provides a defensible foundation for later model, post-training, distributed-training and performance experiments, without claiming cross-machine reproducibility or production readiness.
