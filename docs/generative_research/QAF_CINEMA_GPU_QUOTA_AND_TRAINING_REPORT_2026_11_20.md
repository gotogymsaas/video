# QAF Cinema GPU Quota and Training Report
**Date:** 2026-11-20
**Branch/commit:** `main` at `3d26e0d`
**Mode:** read-only Azure inventory and local CPU preparation

## 1. Executive status

- Azure authentication and the `ml` extension are active in the authorized CLI session.
- Azure Machine Learning workspace: `aml-qaf-cinema-training`.
- Region: `eastus2`.
- Subscription: `c6015f72-55d5-4282-ba0b-f02152d798f7`.
- Private network access is disabled for public access and managed outbound isolation is `allow_only_approved_outbound`.
- No active Azure ML compute instances were reported.
- A100 and H100 family limits are zero in the supplied report.
- VM GPU quota rows are zero.
- `Standard NC Family` and `Standard NV Family` report limits of 6 cores, while `used` is `null`.
- A positive AML limit is not proof of usable capacity. The supplied data does not include verified free cores or physical regional availability.
- No GPU training, model download, checkpoint creation, or resource deployment occurred.

## 2. GPU families

Exact SKUs returned for `eastus2` include:

| Family/SKU | Accelerator | VRAM per GPU | Reported state |
|---|---|---:|---|
| `Standard_NC24ads_A100_v4` | A100 PCIe | 80 GB | 0 A100-family cores |
| `Standard_NC96ads_A100_v4` | 4 x A100 PCIe | 80 GB each | 0 A100-family cores |
| `Standard_ND96amsr_A100_v4` | likely 8 x A100 | 80 GB each | 0 A100-family cores |
| `Standard_NC40ads_H100_v5` | H100 NVL | 94 GB | 0 H100-family cores |
| `Standard_NC80adis_H100_v5` | 2 x H100 NVL | 94 GB each | 0 H100-family cores |
| `Standard_ND96isr_H100_v5` | 8 x H100 NVL | 80 GB each | 0 H100-family cores |
| `Standard_NC4as_T4_v3` | T4 | 16 GB | Not enough for documented 32 GB LoRA minimum |
| `Standard_NC16as_T4_v3` / `NC64as_T4_v3` | T4 | 16 GB each | Verify quota separately |
| `Standard_NV6ads_A10_v5` | A10 | 24 GB | Less than recommended training minimum |

VRAM and GPU details are from Microsoft VM size documentation. Exact NC/ND SKU quotas and sponsorship eligibility must come from the subscription.

## 3. `used: null` interpretation

`used: null` is returned in the current Azure ML list-usage payload for NC/NV families with limits of 6. It means the response did not supply a numeric usage value that this auditor could subtract from limit. It is not evidence of free cores and must not be used as a capacity grant.

The auditor now:

- parses numeric usage and limits, including numeric strings;
- represents `limit=-1` as unverified;
- calculates free cores only when both numeric usage and limit are available;
- treats zero limit plus unknown usage as zero quota;
- requires `free_cores > 0` before declaring a family possible.

## 4. Private network diagnosis

The inventory confirms:

- VNet `vnet-pe-eastus2` exists.
- Subnet `snet-pe` exists.
- No VNet peerings were reported.
- AML and dependency Private Endpoints report Approved status.
- Public access is disabled.

This proves configuration at the resource level, but not Mac DNS resolution or private route connectivity. Required checks, without resource changes:

```bash
az network private-dns zone list --subscription <subscription-id> -o table
az network private-dns link vnet list \
  --subscription <subscription-id> \
  --resource-group <private-dns-zone-rg> \
  --zone-name <zone-name> -o table
az network private-endpoint dns-zone-group list \
  --resource-group rg-qaf-cinema-training \
  --endpoint-name pe-qaf-aml-operator \
  --subscription <subscription-id>
nslookup <workspace-private-fqdn>
nslookup <workspace-regional-fqdn>
```

Use one Point-to-Site VPN or routed jump host for the Mac. Do not enable public workspace access as a shortcut.

## 5. CPU preparation

The repository can progress without GPU:

- Confirm the 106 candidate inventory and metadata.
- Complete FFprobe/decode audit on the original videos.
- Complete identity, session, garment and exercise grouping.
- Obtain independent legal and consent records.
- Assign leakage-free train/validation/test splits.
- Extract reference frames and verify 8n+1 or 4n+1 buckets.
- Generate LTX export metadata.
- Validate the dry-run GPU runner and benchmark protocol.

The current runtime has no NVIDIA GPU and no `nvidia-smi`. The official LTX documentation in this repository requires CUDA, Python 3.12+, 32 GB VRAM minimum with low-VRAM adjustments and 80 GB recommended for standard training.

## 6. Pilot design

Use LTX-2.5 I2V LoRA against the same base model:

1. Start with a small, approved micro-corpus.
2. Keep test subjects and garments absent from train and validation.
3. Use the official dev checkpoint and matching Gemma/VAEs.
4. Use fixed seeds and matched compute for baseline versus LoRA.
5. Generate five-second clips.
6. Require human blind review and temporal/identity/garment checks.
7. Verify the checkpoint hash and run real inference.
8. Stop by a hard GPU-hour budget.

Do not describe CinemaVAE/VideoDiT synthetic results as trained cinematic video.

## 7. Quota recommendation

The best first production candidate is a 1-GPU H100 94 GB SKU only if the sponsorship permits it and a quota increase is approved. It is preferable to an A100 only when actual regional availability and sponsorship pricing are confirmed.

The most prudent pilot request is:

- 1 GPU node.
- Family `Standard NCadsH100v5`.
- Recommended SKU `Standard_NC40ads_H100_v5` or an A100 alternative.
- 40 cores for NC H100 family, subject to the exact regional/quota policy.
- 1 to 2 GPU-hours for a bounded smoke run.
- 8 to 24 GPU-hours for the first LoRA pilot.
- maximum 24 GPU-hours and explicit destroy-on-completion.

These core figures are a request draft, not Azure quota evidence.

## 8. Blockers

1. A100/H100 family quota is zero.
2. NC/NV limit-6 families have unknown numeric usage.
3. Regional physical capacity is unverified.
4. Sponsorship GPU eligibility is unverified.
5. Sponsorship prices are unverified.
6. The 106 media audit has not produced verified decode metadata.
7. Actor, garment and session grouping is incomplete.
8. Independent consent and commercial license evidence is incomplete.
9. Private DNS/VPN/Mac route connectivity is untested.

## 9. Official references

- [Azure ML manage resources and quotas](https://learn.microsoft.com/azure/machine-learning/how-to-manage-quotas)
- [Azure ML REST quotas](https://learn.microsoft.com/rest/api/azureml/quotas/list)
- [Azure NC GPU VM family](https://learn.microsoft.com/azure/virtual-machines/sizes/gpu-accelerated/nc-family)
- [Azure private network security overview](https://learn.microsoft.com/azure/machine-learning/how-to-network-security-overview)
- [Azure ML private endpoint configuration](https://learn.microsoft.com/azure/machine-learning/how-to-configure-private-link)
