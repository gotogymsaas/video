Subject: GPU quota request for limited QAF Cinema LoRA training pilot

Hello Azure Sponsorship Support,

We are requesting quota review for a limited, fail-closed LoRA training pilot for the QAF Cinema project.

Project and subscription:

- Subscription: `c6015f72-55d5-4282-ba0b-f02152d798f7`
- Azure ML workspace: `aml-qaf-cinema-training`
- Resource group: `rg-qaf-cinema-training`
- Region: `eastus2`
- Existing VNet: `vnet-pe-eastus2`
- Public workspace access: disabled
- Managed network isolation: approved outbound only
- Private Endpoints: installed and Approved

The project is preparing a commercial, cinema-oriented image-to-video LoRA adaptation. The first phase will be a bounded five-second inference experiment over authorized GoToGym footage. The data will remain in private Azure storage and be limited to a single controlled Azure ML job.

Requested GPU capacity:

- First-choice family: `Standard NCadsH100v5`
- Alternative family: `Standard NCADS_A100_v4`
- Preferred SKUs: `Standard_NC40ads_H100_v5` or `Standard_NC24ads_A100_v4`
- Requested capacity: one GPU node for the pilot
- Initial approval target: 40 vCPUs for the NC H100 family or the equivalent A100 family quota
- Pilot duration: 8 to 24 GPU-hours
- Maximum initial hard cap: 24 GPU-hours
- Second-stage duration, if approved: no more than 100 GPU-hours

Technical justification:

- Reproducible LoRA adaptation with a matching base-model baseline
- Fixed-seed, leakage-controlled train/validation/test splits
- Private model and media assets
- No public web or dataset exposure
- Maximum VRAM target: at least 80 GB for H100/A100 experimentation
- Automated stop, checkpoint validation, and destroy-on-completion controls
- Human evaluation of identity, garments, movement, continuity and five-second visual quality

Commercial justification:

The project will support authorized cinematic production for GoToGym and is not designed for public training without independent legal review. A limited pilot will let us measure real compute cost, GPU utilization and image-to-video quality before larger investment.

Please confirm:

1. GPU quota currently assigned in the subscription for East US 2.
2. Free quota, separate from current usage.
3. Sponsorship eligibility for H100 and/or A100 NC families.
4. Whether alternate regions are approved for the same families.
5. Hourly or metered cost applicable under this Sponsorship subscription.
6. Any dedicated approval process for GPU quota increases.
7. The process and lead time for a quota increase.

Please also confirm whether a T4 or A10 low-cost fallback can meet an official low-VRAM LoRA configuration, while noting that repository documentation identifies 32 GB VRAM as a minimum with adjustments and 80 GB as recommended.

Budget controls:

- No provisioning before written approval of quota and sponsorship coverage.
- No recurring compute resource or idle GPU.
- One low-cost smoke run before the full pilot.
- Complete resource deletion after the job.
- Alert and hard-stop thresholds for GPU-hours and cost.
- No storage, network or private endpoint changes in the pilot request.
