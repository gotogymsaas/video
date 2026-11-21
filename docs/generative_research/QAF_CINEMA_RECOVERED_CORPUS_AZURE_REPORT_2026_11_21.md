# QAF Cinema Recovered Corpus and Azure Execution Report
**Date:** 2026-11-21
**Repository commit:** `f128d7019374155557a9c8be2a15def2b0bdbd53`
**Status:** private corpus reconciliation and CPU pose preparation completed; no GPU training or Azure resource deployment

## 1. Recovered source corpus

The private repository `gotogymsaas/appdesplegada` is now accessible from the Codespace.

- Repository default branch: `main`.
- Private source commit inspected: `4fb8f911ed18506f7b866c8ed8f537b14d712080`.
- Inventory entries: 106.
- Private MP4 files found: 106.
- Missing inventory entries: 0.
- Size matches: 106/106.
- Git blob SHA matches: 106/106.
- FFprobe/FFmpeg technical failures: 0.
- Full data-intelligence audit: 106 present, 0 missing, 0 failed.

The ten previously missing exercise clips are present:

`bench_press`, `bent_over_row`, `bodyweight_squat`, `deadlift`, `lunge`,
`overhead_press`, `plank`, `pull_up`, `push_up`, `single_leg_rdl`.

The private originals remain outside the public repository.

## 2. MediaPipe Pose observations

The official MediaPipe Pose Landmarker heavy task model was downloaded and
checksummed:

- SHA-256: `64437af838a65d18e5ba7a0d39b465540069bc8aae8308de3e318aad31fcbc7b`.
- Runtime: Python 3.12 on CPU.
- Native EGL runtime: installed.

Real observations were extracted for all ten named exercise clips at 540x960:

- Timeline frames: 1914.
- Frames with at least one named pose detection: 1001.
- Clips with an available 8D Phi_Q vector: 8.
- Clips insufficient for the 8D vector: 2 (`bench_press`, `deadlift`).

Per-clip pose coverage:

| Clip | Timeline frames | Pose frames | 8D available | Coverage |
|---|---:|---:|---|---:|
| bench_press | 192 | 0 | No | 0.0000 |
| bent_over_row | 192 | 186 | Yes | 0.9688 |
| bodyweight_squat | 192 | 150 | Yes | 0.7812 |
| deadlift | 192 | 1 | No | 0.0052 |
| lunge | 186 | 92 | Yes | 0.4946 |
| overhead_press | 192 | 119 | Yes | 0.6198 |
| plank | 192 | 175 | Yes | 0.9115 |
| pull_up | 192 | 44 | Yes | 0.2292 |
| push_up | 192 | 56 | Yes | 0.2917 |
| single_leg_rdl | 192 | 178 | Yes | 0.9271 |

The pose implementation uses official MediaPipe joint IDs. It does not infer
depth, cloth dynamics or segmentation.

## 3. IC-LoRA pilot pairs

Ten private named-clips were normalized to 544x960, 24 fps and a 186 to 192
frame range. A pose skeleton reference video was generated for each target.

- Paired samples: 10.
- Samples with 8D metadata: 8.
- Target/reference frame counts verified for each pair.
- Target/reference FPS verified for each pair.
- Target and reference SHA-256 values verified.
- The 8D vector is metadata only and is not a direct LTX condition.
- No real LTX weights or training run were downloaded or executed.

The official LTX V2V IC-LoRA dataset convention and flexible reference
condition were emitted by the repository adapter.

The earlier ten WhatsApp pilot clips also produced real named pose observations
and the private pair adapter validated them; neither pilot set constitutes
proof of cinematic quality or QAF superiority.

## 4. Private network state

Live Azure read-only inspection confirmed:

- Subscription active and Enabled.
- Azure ML workspace public network access: Disabled.
- Managed isolation: `allow_only_approved_outbound`.
- Azure ML Private Endpoint: approved.
- Private DNS zone `privatelink.api.azureml.ms`: provisioned.
- Private DNS VNet link: linked to `vnet-pe-eastus2`.
- Private DNS records include AML API and notebook endpoints.
- No Azure ML compute instances are active.

No private network resource was changed.

## 5. GPU and cost state

Live East US 2 SKU inspection shows A100, H100 and T4 SKUs:

| SKU | VRAM | East US 2 official retail consumption |
|---|---:|---:|
| `Standard_NC24ads_A100_v4` | 1 x 80 GB | $4.777/hour |
| `Standard_NC40ads_H100_v5` | 1 x 94 GB | $8.820/hour |
| `Standard_NC4as_T4_v3` | 1 x 16 GB | $0.526/hour |

Official Spot meters were also visible. They are not a guaranteed cost or
capacity contract and may be evicted.

AML quota report remains incomplete for the NC/NV families:

- A100 family limit: 0.
- H100 family limit: 0.
- VM GPU families: 0.
- `standardNCFamily` limit: 6, usage `null`.
- `standardNVFamily` limit: 6, usage `null`.

No free GPU cores can be claimed from usage `null`. Sponsorship GPU eligibility
and Sponsorship credit coverage remain unverified.

No GPU, VM, cluster, endpoint or storage resource was created.

## 5A. CPU capacity and low-cost preparation

The live quota queries distinguish CPU from GPU capacity:

- Azure VM regional general-vCPU limit: 65; reported regional usage: 0, thus a 65-vCPU general regional quota headroom at the time of the query.
- Azure ML reported CPU quota categories include 350 dedicated cores, 200 cluster limit and 100 low-priority cores. These are quota figures, not a guarantee of per-family SKU capacity or a single interchangeable pool.
- Separate GPU family quotas for A100/H100 remain at zero.
- Local Codespace: 2 vCPU visible, AMD EPYC host, Linux/CUDA unavailable.

CPU is therefore sufficient for continuing data preparation. It is not evidence
of GPU availability. Use the Mac or the Codespace for FFprobe, pose extraction,
guide rendering and paired-manifest validation; do not start a paid Azure CPU
compute resource unless CPU processing is measurably slower than local
processing.

## 5B. Mac suitability

The supplied Mac is a 16-inch 2021 MacBook Pro with Apple M1 Pro and 16 GB of
unified memory. It is suitable for:

- FFprobe and FFmpeg preparation.
- MediaPipe Pose CPU extraction.
- Pose-guide rendering.
- Pair manifest and integrity validation.
- Human visual review and matched-benchmark annotation.

It is not a recommended host for official LTX training:

- The official LTX trainer requires Linux with CUDA.
- macOS does not expose the supported CUDA/Triton environment.
- The low-VRAM official path is oriented toward 32 GB GPUs.
- 16 GB unified memory is below the documented low-VRAM target.

Apple Silicon should be used for CPU preparation and inference experiments
only when a separately tested, compatible implementation exists. It should not
be used to claim a successful official LTX-LoRA training run.

The retail pricing lookup for East US 2 returned multiple meter values for the `Standard_D4s_v5` SKU, including USD 0.376/hour and USD 0.192/hour for separately labeled consumption meters, plus Spot and low-priority variants. The correct actual payable rate **cannot be determined from the SKU name alone**; query the exact operating system, offer, meter and billing model in Azure before estimating costs. This is not a quotation or sponsorship eligibility check.

Processing on the Mac does not create an Azure VM charge. GitHub Codespaces can have separate compute and storage charges under GitHub billing. Do not start an Azure CPU VM solely because Azure credits exist. If CPU cloud compute becomes necessary, require a measured local bottleneck, verified SKU compatibility, explicit run-hour ceiling and actual stop/deallocation, since budget alerts alone do not suspend spending.

**Data provenance:** These CPU/Mac observations were reported by Copilot from authenticated Azure CLI and hardware details; this document update does not re-query Azure and does not establish current free quota or sponsorship credit coverage.

## 6. Test evidence

The following local suites passed:

- 31 QAF Data Intelligence, pose-guide, IC-LoRA adapter and Azure auditor tests.
- Private reconciliation: 106/106 found, size match and Git blob match.
- Private pose extraction: 1914 named-exercise frames and 1001 detected pose frames.
- IC-LoRA adapter: 10 named pairs validated.

No test establishes training quality or QAF superiority.

## 7. Remaining blockers

1. Sponsorship GPU eligibility is not verified.
2. A100/H100 quotas are zero.
3. NC/NV limit-6 usage is unknown.
4. No real GPU training or physical SKU capacity has been tested.
5. Independent consent and commercial licensing records are still required.
6. Actor, session and garment splits are incomplete.
7. Cinematic visual references require approved professional footage.
8. No matched baseline/QAF training experiment has run.

## 8. Next executable step

Prepare a written quota request for one low-VRAM or one A100 pilot. Before
submission, obtain Sponsorship eligibility and budget limits. If approved,
run a bounded smoke test with:

- one matching scene;
- fixed seeds;
- base LTX;
- visual LoRA;
- classical pose control;
- QAF planning plus the same pose control;
- matched compute budget;
- blind human review;
- real MP4 and checkpoint validation.
