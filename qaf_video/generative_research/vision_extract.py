"""Extract real MediaPipe pose/hand observations from a locally authorized MP4.

Video decoding is FFmpeg CPU; optional official .task model files must be
installed by the operator. No claims about depth or segmentation are emitted.
"""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from PIL import Image
from ..core import require,probe,sha256
from .vision_evidence import mediapipe_extract,validate_observations

def decode_frames(source,width,height,fps,count):
    require(width%2==0 and height%2==0 and 128<=width<=1920 and 128<=height<=1920,
            "Invalid extraction dimensions")
    require(1<=fps<=60 and 1<=count<=1200,"Invalid extraction schedule")
    path=Path(source).resolve()
    require(path.is_file() and path.suffix.lower()==".mp4","Local MP4 required")
    info=probe(path)
    require(float(info["format"]["duration"])+.05 >= (count-1)/fps,
            "Video shorter than requested frame schedule")
    size=width*height*3
    args=["ffmpeg","-nostdin","-v","error","-i",str(path),
          "-vf",f"fps={fps},scale={width}:{height}:flags=bicubic",
          "-frames:v",str(count),"-pix_fmt","rgb24","-f","rawvideo","pipe:1"]
    process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    result=[]
    try:
        for index in range(count):
            blob=process.stdout.read(size)
            require(len(blob)==size,"Input MP4 has insufficient frames")
            result.append(Image.frombytes("RGB",(width,height),blob))
        process.stdout.close()
        error=process.stderr.read().decode(errors="replace")
        require(process.wait(timeout=60)==0,"FFmpeg decode: "+error[-300:])
    finally:
        if process.poll() is None:process.kill();process.wait()
    return result

def extract_mp4(video,pose_task,output,width,height,fps,count,hand_task=None,
                confidence=.45):
    frames=decode_frames(video,width,height,fps,count)
    result=mediapipe_extract(frames,pose_task,hand_task,confidence)
    validate_observations(result,Path(output).resolve().parent,count,width,height)
    result["source_mp4_sha256"]=sha256(video)
    result["model_evidence"]="MediaPipe Tasks IMAGE-mode framewise inference"
    result["consent_certified"]=False
    result["depth_estimated"]=False
    result["segmentation_estimated"]=False
    output=Path(output).resolve()
    require(output.suffix.lower()==".json","Expected JSON observation output")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return {"output":str(output),"frames":count,"observed_pose_frames":
            sum(bool(x["pose"]) for x in result["timeline"]),
            "observed_hand_frames":sum(bool(x["hands"]) for x in result["timeline"]),
            "requires_external_mask_and_depth":True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video");p.add_argument("--pose-task",required=True)
    p.add_argument("--hand-task");p.add_argument("--out",required=True)
    p.add_argument("--width",type=int,default=960)
    p.add_argument("--height",type=int,default=540)
    p.add_argument("--fps",type=int,default=24)
    p.add_argument("--frames",type=int,default=192)
    p.add_argument("--confidence",type=float,default=.45)
    a=p.parse_args()
    print(json.dumps(extract_mp4(a.video,a.pose_task,a.out,a.width,a.height,
         a.fps,a.frames,a.hand_task,a.confidence),indent=2))
if __name__=="__main__":main()
