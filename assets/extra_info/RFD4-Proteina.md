## Additional information on RFD4-Proteina evaluation results

The metadata contains six versions of RFD4-Proteina information on MotifBench (indexed / unindexed + low/medium/high-thinking). For more information please refer to [GitHub repo](https://github.com/Jetzu/RFD4-MotifBench).

### RFD4-Proteina detailed results

The main leaderboard records _unindexed + high-thinking_ mode. All the associated metadata could be found in the [Zenodo link](https://zenodo.org/records/23942848).

| Mode      | Thinking        | MotifBench Score | Runtime (per scaffold)             |
| --------- | --------------- | ---------------- | ---------------------------------- |
| Unindexed | medium-thinking | 60.36 ± 0.87     | ~8 s (NVIDIA RTX A5000 / RTX 4090) |
| Unindexed | high-thinking   | 60.21 ± 0.57     | ~7.6 s (NVIDIA L40S)               |
| Unindexed | low-thinking    | 58.64 ± 1.21     | ~3.9 s (NVIDIA L40S)               |
| Indexed   | high-thinking   | 55.28 ± 0.16     | ~7.5 s (NVIDIA L40S)               |
| Indexed   | medium-thinking | 55.06 ± 1.35     | ~8 s (NVIDIA RTX A5000 / RTX 4090) |
| Indexed   | low-thinking    | 53.95 ± 1.00     | ~4.0 s (NVIDIA L40S)               |

\* Items sorted by score. Generation times include model loading and compilation and were measured on the GPUs shown.