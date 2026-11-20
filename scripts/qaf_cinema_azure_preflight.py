"""QAF Cinema: read-only Azure ML, network and GPU quota inventory.

No resource creation, model downloads, changes to isolation, or GPU use.
Requires an authenticated Azure CLI session with the ml extension preinstalled.
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def az_read(args):
    env = dict(os.environ, AZURE_EXTENSION_USE_DYNAMIC_INSTALL="no")
    try:
        p = subprocess.run(["az", *args, "--output", "json", "--only-show-errors"],
                           env=env, capture_output=True, text=True, timeout=90)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(type(exc).__name__) from exc
    if p.returncode:
        raise RuntimeError("AZ_CLI_FAILED_EXIT_" + str(p.returncode))
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AZ_CLI_INVALID_JSON") from exc

def get(obj, *keys, default=None):
    if isinstance(obj, dict):
        for key in keys:
            if key in obj:
                return obj[key]
    return default

def gpu_quotas(rows):
    result = []
    for row in rows if isinstance(rows, list) else []:
        name = get(row, "name", default="")
        if isinstance(name, dict):
            name = get(name, "localizedValue", "localized_value", "value", default="")
        if not re.search(r"\b(?:standard[ _-]*)?(?:nc|nd|nv)[a-z0-9_ -]*", str(name), re.I):
            continue
        used, limit = get(row, "currentValue", "current_value"), get(row, "limit")
        free = limit-used if isinstance(limit, (float, int)) and isinstance(used, (float, int)) else None
        result.append({"family": name, "used_cores": used, "limit_cores": limit, "free_cores": free})
    return result

def collect(subscription, rg="rg-qaf-cinema-training",
            workspace="aml-qaf-cinema-training", region="eastus2",
            vnet="vnet-pe-eastus2", run=az_read):
    report = {"schema": "qaf_cinema_azure_preflight_v1",
              "captured_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "READ_ONLY", "subscription": subscription,
              "resource_group": rg, "workspace": workspace,
              "region": region, "vnet": vnet,
              "checks": {}, "errors": {}, "training_performed": False,
              "pricing": "UNVERIFIED", "sponsorship_gpu_eligibility": "UNVERIFIED"}
    def probe(key, args):
        try:
            return run(args)
        except (RuntimeError, OSError, ValueError) as exc:
            report["errors"][key] = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
            return None
    account = probe("account", ["account", "show"])
    if not isinstance(account, dict):
        report["decision"] = "BLOCKED_AZURE_AUTH_REQUIRED"
        return report
    if str(get(account, "id", default="")).lower() != subscription.lower():
        report["decision"] = "BLOCKED_WRONG_ACTIVE_SUBSCRIPTION"
        return report
    if str(get(account, "state", default="")).lower() != "enabled":
        report["decision"] = "BLOCKED_SUBSCRIPTION_NOT_ENABLED"
        return report
    report["checks"]["subscription_active"] = True
    scope = ["--subscription", subscription]
    extension = probe("ml_extension", ["extension", "show", "--name", "ml"])
    report["checks"]["ml_extension_present"] = isinstance(extension, dict)
    if isinstance(extension, dict):
        shared = ["--resource-group", rg, "--workspace-name", workspace, *scope]
        ws = probe("workspace", ["ml", "workspace", "show",
                  "--resource-group", rg, "--name", workspace, *scope])
        if isinstance(ws, dict):
            managed = get(ws, "managed_network", "managedNetwork", default={})
            report["checks"]["workspace"] = {
                "public_network_access": get(ws, "public_network_access", "publicNetworkAccess", default="UNKNOWN"),
                "isolation_mode": get(managed, "isolation_mode", "isolationMode", default="UNKNOWN"),
                "provisioning_state": get(ws, "provisioning_state", "provisioningState", default="UNKNOWN")}
        computes = probe("compute", ["ml", "compute", "list", *shared])
        if isinstance(computes, list):
            report["checks"]["aml_computes"] = [
                {"name": get(x, "name"), "type": get(x, "type"),
                 "size": get(x, "size", default="UNKNOWN")} for x in computes]
        usage = probe("aml_usage", ["ml", "compute", "list-usage", *shared, "--location", region])
        if isinstance(usage, list):
            report["checks"]["aml_gpu_quotas"] = gpu_quotas(usage)
        sizes = probe("aml_sizes", ["ml", "compute", "list-sizes", *shared, "--location", region])
        if isinstance(sizes, list):
            report["checks"]["gpu_skus_listed"] = sorted({
                str(get(x, "name", default="")) for x in sizes
                if re.match(r"^standard_(nc|nd|nv)", str(get(x, "name", default="")), re.I)})
    networks = probe("vnets", ["network", "vnet", "list", *scope])
    if isinstance(networks, list):
        report["checks"]["matching_vnets"] = [
            {"name": get(n, "name"),
             "subnets": [get(s, "name") for s in get(n, "subnets", default=[])],
             "peerings": len(get(n, "virtualNetworkPeerings", "virtual_network_peerings", default=[]) or [])}
            for n in networks if str(get(n, "name", default="")).lower() == vnet.lower()]
    endpoints = probe("private_endpoints", ["network", "private-endpoint", "list", *scope])
    if isinstance(endpoints, list):
        found = []
        for endpoint in endpoints:
            sid = str(get(get(endpoint, "subnet", default={}), "id", default="")).lower()
            if "/virtualnetworks/" + vnet.lower() + "/" not in sid:
                continue
            links = (get(endpoint, "privateLinkServiceConnections", "private_link_service_connections", default=[]) or [])
            links += (get(endpoint, "manualPrivateLinkServiceConnections", "manual_private_link_service_connections", default=[]) or [])
            found.append({"name": get(endpoint, "name"), "states": [
                get(get(link, "privateLinkServiceConnectionState", "private_link_service_connection_state", default={}),
                    "status", default="UNKNOWN") for link in links]})
        report["checks"]["private_endpoints_in_vnet"] = found
    vm = probe("vm_usage", ["vm", "list-usage", "--location", region, *scope])
    if isinstance(vm, list):
        report["checks"]["vm_gpu_quotas"] = gpu_quotas(vm)
    aml = report["checks"].get("aml_gpu_quotas")
    report["decision"] = (
        "INCOMPLETE_AML_GPU_QUOTA_NOT_VERIFIED" if aml is None else
        "BLOCKED_NO_FREE_AML_GPU_CORES_REPORTED" if not any(
            isinstance(q["free_cores"], (int, float)) and q["free_cores"] > 0 for q in aml)
        else "POSSIBLE_GPU_QUOTA_NEEDS_SKU_AND_BILLING_VALIDATION")
    report["limitations"] = [
        "No Mac-to-private-endpoint DNS or VPN connectivity test",
        "Azure VM quota differs from Azure ML managed-compute quota",
        "GPU SKU listing does not guarantee physical capacity or VRAM",
        "Sponsorship coverage and GPU pricing must be verified separately"]
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subscription", required=True)
    p.add_argument("--resource-group", default="rg-qaf-cinema-training")
    p.add_argument("--workspace", default="aml-qaf-cinema-training")
    p.add_argument("--region", default="eastus2")
    p.add_argument("--vnet", default="vnet-pe-eastus2")
    p.add_argument("--out", type=Path, help="Private report path; do not commit this report")
    args = p.parse_args()
    report = collect(args.subscription, args.resource_group, args.workspace,
                     args.region, args.vnet)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        if args.out.exists():
            p.error("Output already exists; use a new name for each audit")
        args.out.write_text(result, encoding="utf8")
    print(result)
    return 0 if report["decision"].startswith("POSSIBLE") else 2

if __name__ == "__main__":
    raise SystemExit(main())
