"""Guarded execution of locally installed official I2V LoRA trainer.

GPU execution is strictly opt-in; never executes during CI or imports.
No weights or copyrighted training media are downloaded by this module.
"""
from __future__ import annotations
import json,os,subprocess,time
from pathlib import Path
from ..core import require,sha256
from .neural_program import plan_program

def cuda_devices():
    result=subprocess.run(["nvidia-smi","--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits"],capture_output=True,text=True,timeout=15,
        check=False)
    require(result.returncode==0,"No accessible NVIDIA GPU: "+result.stderr[-300:])
    rows=[]
    for row in result.stdout.strip().splitlines():
        fields=row.rsplit(",",1)
        require(len(fields)==2,"Unexpected nvidia-smi output")
        name,ram=fields
        rows.append({"name":name.strip(),"vram_mib":int(ram.strip())})
    require(rows,"No GPUs detected")
    return rows

def training_execution(manifest,workspace,output_dir,execute=False,min_vram_mib=32000):
    plan=plan_program(manifest,workspace)
    if not execute:
        return {"status":"DRY_RUN_ONLY","gpu_training_completed":False,
                "config_sha256":plan["trainer_config_sha256"],
                "dataset_sha256":plan["dataset_sha256"],
                "command":plan["preflight_argv"],"cpu_or_gpu_use":0}
    require(os.environ.get("QAF_CINEMA_ALLOW_GPU_TRAINING")=="YES",
            "Set QAF_CINEMA_ALLOW_GPU_TRAINING=YES after approving costs")
    require(type(min_vram_mib)==int and 16000<=min_vram_mib<=256000,
            "Invalid VRAM threshold")
    devices=cuda_devices()
    require(max(d["vram_mib"] for d in devices)>=min_vram_mib,
            "No GPU reaches required VRAM")
    out=Path(output_dir).resolve()
    root=Path(workspace).resolve()
    require(out.is_relative_to(root),"Output must remain inside private workspace")
    require(not out.exists() or not list(out.iterdir()),"Use a fresh empty output directory")
    out.mkdir(parents=True,exist_ok=True)
    log=out/"trainer.log"
    args=plan["preflight_argv"]
    timeout=max(300,int(plan["max_gpu_hours"]*3600))
    started=time.monotonic()
    # Installer and all project dependencies must be manually reviewed.
    # Restrict executable to known literal argv and official script.
    require(args[:3]==["uv","run","python"] and args[3]=="scripts/train.py",
            "Unsupported GPU training invocation")
    with log.open("wb") as handle:
        try:
            completed=subprocess.run(args,cwd=plan["cwd"],stdout=handle,
                     stderr=subprocess.STDOUT,timeout=timeout,check=False)
            code=completed.returncode
        except subprocess.TimeoutExpired:
            code=124
    elapsed=time.monotonic()-started
    # Trainer's working directory may save checkpoints elsewhere per YAML;
    # require explicit post-run checkpoint attestation from a reviewer.
    report={"schema":"qaf_gpu_training_attempt_v1","status":"FINISHED_EXIT_ZERO_UNVERIFIED" if code==0 else "FAILED_OR_TIMED_OUT",
       "exit_code":code,"gpu_training_completed":False,
       "checkpoint_independently_verified":False,
       "trainer_log_sha256":sha256(log),
       "elapsed_seconds":round(elapsed,2),"cuda_devices":devices,
       "dataset_sha256":plan["dataset_sha256"],
       "training_config_sha256":plan["trainer_config_sha256"],
       "max_gpu_hours":plan["max_gpu_hours"],
       "next_gate":"Inspect actual LoRA artifact, validation logs, weights checksum and matched baseline before claiming trained."}
    (out/"training_attempt.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("program");p.add_argument("--workspace",required=True)
    p.add_argument("--output-dir",required=True)
    p.add_argument("--execute",action="store_true",help="Explicit approval + GPU guard")
    args=p.parse_args()
    print(json.dumps(training_execution(args.program,args.workspace,args.output_dir,
                                      execute=args.execute),indent=2))
if __name__=="__main__":main()
