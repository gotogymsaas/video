"""Offline tests for read-only QAF Cinema Azure preflight."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts/qaf_cinema_azure_preflight.py"
spec = importlib.util.spec_from_file_location("qaf_azure_preflight", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SUB = "00000000-0000-0000-0000-000000000001"

class FakeAzure:
    def __init__(self, free_cores=0, extension=True):
        self.calls = []
        self.free_cores = free_cores
        self.extension = extension

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[:2] == ["account", "show"]:
            return {"id": SUB, "state": "Enabled", "credential": "MUST_NOT_BE_REPORTED"}
        if argv[:2] == ["extension", "show"]:
            if not self.extension:
                raise RuntimeError("ML_EXTENSION_MISSING")
            return {"name": "ml"}
        if argv[:3] == ["ml", "workspace", "show"]:
            return {"public_network_access": "Disabled",
                    "managed_network": {"isolation_mode": "AllowOnlyApprovedOutbound"}}
        if argv[:3] == ["ml", "compute", "list-usage"]:
            return [{"name": {"value": "Standard NCADSA100v4 Family vCPUs"},
                     "currentValue": 0, "limit": self.free_cores}]
        if argv[:3] == ["ml", "compute", "list-sizes"]:
            return [{"name": "Standard_NC24ads_A100_v4"}]
        if argv[:3] == ["ml", "compute", "list"]:
            return []
        if argv[:3] == ["network", "vnet", "list"]:
            return [{"name": "vnet-pe-eastus2", "subnets": [{"name": "snet-pe"}],
                     "virtualNetworkPeerings": []}]
        if argv[:3] == ["network", "private-endpoint", "list"]:
            return [{"name": "pe-aml",
                     "subnet": {"id": "/virtualNetworks/vnet-pe-eastus2/subnets/snet-pe"},
                     "privateLinkServiceConnections": [
                          {"privateLinkServiceConnectionState": {"status": "Approved"}}]}]
        if argv[:2] == ["vm", "list-usage"]:
            return []
        raise AssertionError("Unexpected command: " + str(argv))

class Tests(unittest.TestCase):
    def test_zero_quota_blocks_without_exposing_credentials(self):
        fake = FakeAzure()
        report = module.collect(SUB, run=fake)
        self.assertEqual(report["decision"], "BLOCKED_NO_FREE_AML_GPU_CORES_REPORTED")
        self.assertEqual(report["checks"]["workspace"]["isolation_mode"], "AllowOnlyApprovedOutbound")
        self.assertEqual(report["checks"]["private_endpoints_in_vnet"][0]["states"], ["Approved"])
        self.assertNotIn("MUST_NOT_BE_REPORTED", str(report))
        self.assertFalse(any("create" in x or "start" in x or "delete" in x
                             for cmd in fake.calls for x in cmd))

    def test_available_quota_does_not_claim_training_or_sponsorship(self):
        report = module.collect(SUB, run=FakeAzure(free_cores=24))
        self.assertTrue(report["decision"].startswith("POSSIBLE"))
        self.assertFalse(report["training_performed"])
        self.assertEqual(report["sponsorship_gpu_eligibility"], "UNVERIFIED")

    def test_missing_ml_extension_fails_closed(self):
        fake = FakeAzure(extension=False)
        report = module.collect(SUB, run=fake)
        self.assertEqual(report["decision"], "INCOMPLETE_AML_GPU_QUOTA_NOT_VERIFIED")
        self.assertFalse(report["checks"]["ml_extension_present"])
        self.assertFalse(any("add" in cmd for cmd in fake.calls))

    def test_wrong_subscription_stops_before_inventory(self):
        fake = FakeAzure()
        report = module.collect("22222222-2222-2222-2222-222222222222", run=fake)
        self.assertEqual(report["decision"], "BLOCKED_WRONG_ACTIVE_SUBSCRIPTION")
        self.assertEqual(len(fake.calls), 1)

    def test_gpu_quota_filter(self):
        rows = [{"name": {"value": "Standard NC Family vCPUs"},
                 "currentValue": 3, "limit": 4},
                {"name": {"value": "Standard D Family vCPUs"},
                 "currentValue": 0, "limit": 20}]
        result = module.gpu_quotas(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["free_cores"], 1)

if __name__ == "__main__":
    unittest.main()
