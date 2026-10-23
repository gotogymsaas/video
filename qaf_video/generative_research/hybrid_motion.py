"""Hybrid moving-shot connector: composite externally generated MP4 with QAF VFX.
The original video is decoded frame-by-frame; no motion generation is claimed.
"""
import json,subprocess
from pathlib import Path
from PIL import Image
from ..core import require,probe,sha256
from .hybrid_vfx import load_spec,frame
from .vision_evidence import read_observations, per_frame_evidence, anchor_point, depth_occlusion_mask
from .editorial_timeline import load_timeline,quad_at,claims_at

def render_motion(project,video,output,observations=None,editorial=None):
    project=Path(project).resolve()
    spec,root=load_spec(project)
    source=Path(video).resolve()
    require(source.is_file() and source.suffix.lower()==".mp4","Existing MP4 required")
    require(source.is_relative_to(root),"Video must belong to project workspace")
    meta=probe(source)
    require(float(meta["format"]["duration"])+0.05>=spec["seconds"],"Video too short")
    dest=Path(output).resolve()
    require(dest.suffix.lower()==".mp4" and dest!=source,"Invalid MP4 output")
    dest.parent.mkdir(parents=True,exist_ok=True)
    width,height,fps=spec["width"],spec["height"],spec["fps"]
    frames=round(fps*spec["seconds"]);size=width*height*3
    bundle,vision_root=(read_observations(observations,frames,width,height) if observations else (None,None))
    timeline,editorial_hash=(load_timeline(editorial,frames,width,height) if editorial else (None,None))
    reader=subprocess.Popen(["ffmpeg","-nostdin","-v","error","-i",str(source),
       "-vf",f"fps={fps},scale={width}:{height}:flags=bicubic",
       "-frames:v",str(frames),"-pix_fmt","rgb24","-f","rawvideo","pipe:1"],
       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    writer=subprocess.Popen(["ffmpeg","-nostdin","-y","-v","error",
       "-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}","-r",str(fps),
       "-i","pipe:0","-an","-c:v","libx264","-pix_fmt","yuv420p",str(dest)],
       stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for index in range(frames):
            buf=reader.stdout.read(size)
            require(len(buf)==size,"Incomplete source motion clip")
            original=Image.frombytes("RGB",(width,height),buf)
            local_spec=spec
            foreground=None
            if bundle is not None:
                evidence=per_frame_evidence(bundle,vision_root,index)
                if spec.get("hand_follow_energy") is True:
                    center=anchor_point(evidence,"hands")
                    if center is not None:
                        local_spec=dict(spec)
                        local_spec["events"]=[({**event,"center":list(center)}
                            if event["type"]=="pulse" else event)
                            for event in spec.get("events",[])]
                if evidence["mask"] is not None:
                    foreground=depth_occlusion_mask(evidence["mask"],evidence["depth"],
                                   spec.get("depth_threshold",128))
            if timeline is not None:
                local_spec=dict(local_spec)
                local_spec["phone_quad"]=quad_at(timeline,index)
            result,_=frame(local_spec,root,index/fps,background=original,foreground_mask=foreground)
            if timeline is not None:result=claims_at(result,timeline,index)
            writer.stdin.write(result.tobytes())
        writer.stdin.close();writer_error=writer.stderr.read().decode(errors="replace")
        require(writer.wait(timeout=180)==0,"Video encoder: "+writer_error[-500:])
        reader.stdout.close();reader_error=reader.stderr.read().decode(errors="replace")
        require(reader.wait(timeout=90)==0,"Video decoder: "+reader_error[-500:])
    finally:
        for proc in (reader,writer):
            if proc.poll() is None:proc.kill();proc.wait()
    report={"schema":"qaf_hybrid_motion_v1","frames":frames,"input_sha256":sha256(source),
      "output_sha256":sha256(dest),"generated_neural_motion_here":False,
      "human_approval_required":True,"vision_observations_used":bundle is not None,
      "vision_observations_sha256":sha256(observations) if observations else None,
      "editorial_timeline_sha256":editorial_hash}
    dest.with_suffix(".motion.json").write_text(json.dumps(report,indent=2))
    return report
