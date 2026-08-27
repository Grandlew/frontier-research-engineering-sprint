# Day 2 Data Provenance Report

## Scope

This report evaluates a synthetic 16-record reasoning fixture. The claim is limited to reproducible source identity, canonical logical identity, deterministic group-aware splitting, and tested sensitivity to semantic mutation. It does not establish dataset quality or model capability.

## Configuration and schema

- Dataset: `day02-reasoning-fixture`
- Schema version: `1.0.0`
- Fields: `example_id`, `group_id`, `prompt`, `target`
- Split seed: `1729`
- Fractions: train `0.70`, validation `0.15`, test `0.15`
- Configuration fingerprint: `519d3fc62fae3c68adfbff8fc7ff7d8cd6956cab99d4ac16080062231b13aedd`

Paths and run names are operational metadata and are excluded from the configuration fingerprint and deterministic data manifest.

## Dataset identities

- Raw source SHA-256: `ed2f09b0acdc66cba248091838be5ff706d872c87a6fb55e96ba4a7c1424d252`
- Logical dataset SHA-256: `9e4f146e6fc98310dc33aeb7b9380a6d9f2ab58a50e9785b0e4fe6c8f7f2bb1a`
- Deterministic data-manifest file SHA-256: `69d34cc225e672c7e93381b2512ccd49b3beb068b6b8fdd4d4ed232512380544`

The raw hash identifies exact CSV bytes. The logical hash identifies validated records after deterministic split attachment, `example_id` ordering, canonical compact JSON serialization, and UTF-8 encoding.

## Split statistics and isolation

| Split | Records | Unique groups | Split SHA-256 |
|---|---:|---:|---|
| Train | 9 | 8 | `e03765c81c829f9df2739653167291185d42c6c15458179f27c867278fed1361` |
| Validation | 3 | 2 | `b0b05e8b36b163dcb4d6c9067ef0eb30f94be31ed517350d8b0cc86dfb3111f7` |
| Test | 4 | 2 | `03245afe91801828b35955f4ecc4f218cae44ad00a2872b41b2e876336eed0ce` |
| Total | 16 | 12 | — |

Group isolation passed: no `group_id` occurs in more than one split. Normalized-prompt consistency also passed for the fixture.

## Two-run reproducibility

Independent builds `run_a` and `run_b` produced identical source and logical hashes. PowerShell `Get-FileHash` comparisons returned `True` for both `dataset.jsonl` and `data_manifest.json`. The operational `build_manifest.json` files may differ because they contain run names, output paths, creation times, and environment information.

## Controlled permutation and mutation experiment

The original, reversed, and deterministic seed-1729-shuffled collections received identical group-to-split assignments.

| Treatment | Raw CSV SHA-256 | Logical dataset SHA-256 |
|---|---|---|
| Original | `2cc9a88c951910e1fc20d1ee5a725d996d8bb6946a900a2fd57aa5b2fae3b59e` | `12c2e1eb896f0933916388f8409a1349225bc35b0dbc08c2a37f48600150de0d` |
| Reversed | `472a32ecab8c3afc5c9683ab0c0f200285e08aebf7dd4f4377e1870a2ce87a57` | `12c2e1eb896f0933916388f8409a1349225bc35b0dbc08c2a37f48600150de0d` |
| Seed-1729 shuffle | `1a7f64571bd1e28d21346af0246bb5cce2341f209178cb703af36d80650358e7` | `12c2e1eb896f0933916388f8409a1349225bc35b0dbc08c2a37f48600150de0d` |
| One target changed | Not applicable | `5f019b02f19247f9cb312a7b6fedb3f530dfd1bbb39132ee6fbe8c2ea225efde` |

The three physical layouts have distinct raw hashes but one logical digest. Changing one target changes the logical digest, rejecting the competing explanation that logical identity merely reflects raw file layout.

## Deliberate failure and restoration

Sorting was temporarily removed from `canonical_dataset_bytes`. The original provenance test unexpectedly still passed because `attach_splits` had already sorted its output. This revealed a masked component-boundary gap rather than validating the defective serializer.

A direct order-invariance regression test was added. With sorting still removed, it failed as required:

- Input-order digest: `291f1bed7ff4d74c5a5d5cc73a2273d573bbabc23dd064d9d77bd242eca61ff1`
- Reversed-order digest: `1e7212d7e9e829562c026025c01d6614e2df1a6b9f3c7c43a7fad8ab37deb813`

Sorting by `example_id` was restored. The direct regression test then passed, establishing that canonicalization itself—not only its current caller—removes incidental record ordering. The restored full suite passed all six tests.

## Limitations

- The fixture is synthetic and does not demonstrate real-world representativeness or utility.
- SHA-256 identity does not prove correctness, fairness, legality, or absence of bias.
- Group-aware splitting isolates declared groups but cannot detect every semantic duplicate or hidden causal dependency.
- NFKC normalization, whitespace collapsing, and case-folding can merge distinctions that matter in other domains.
- Row-order invariance would be scientifically invalid for sequences where order carries meaning.
- Exact raw hashes can change with line-ending normalization even when logical contents remain equivalent.

## Research-defense answers

1. **Why are raw-file identity and logical-dataset identity both necessary?**  
   Raw identity proves exact source-byte provenance; logical identity proves equivalence after parsing, validation, sorting, and canonicalization.

2. **Why does group-aware splitting reduce leakage without proving the absence of semantic contamination?**  
   It keeps known groups together, but different group IDs can still contain duplicated or semantically overlapping content.

3. **When would row-order invariance be scientifically wrong?**  
   When order affects meaning or behavior, including time series, dialogues, rankings, streams, and order-dependent training procedures.

4. **Why can a dataset have a stable digest while still being mislabeled or biased?**  
   A digest proves consistency, not correctness or fairness; it faithfully identifies stable errors and biases too.

5. **What additional provenance is required for a downloaded public dataset?**  
   Record the source URL, dataset version or revision, retrieval time, license, upstream checksum, download tooling, transformation history, filtering rules, and preferably immutable archive or repository identifiers.
