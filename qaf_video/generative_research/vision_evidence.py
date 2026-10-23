"""Per-frame vision evidence for QAF cinematic VFX.

Opt-in MediaPipe Tasks pose + hand tracking; independently supplied aligned
segmentation and metric/relative depth PNGs. Fails closed on missing models.
No network, no invented 'real depth' from RGB and no face identification.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from PIL import Image
from ..core import require,sha256

SCHEMA="qaf_cinematic_observations_v1"

def _local(root,value):
    require(isinstance(value,str) and bool(value),"Missing local vision asset")
    base=Path(root).resolve();p=(base/value).resolve()
    require(p.is_relative_to(base) and p.is_file(),"Vision asset missing or outside workspace")
    return p

def validate_observations(data,root,frames,width,height):
    require(data.get("schema")==SCHEMA,"Invalid observation schema")
    require(data.get("width")==width and data.get("height")==height,"Observation geometry mismatch")
    require(data.get("frames")==frames,"Observation frame count mismatch")
    records=data.get("timeline")
    require(isinstance(records,list) and len(records)==frames,"Incomplete observation timeline")
    for i,rec in enumerate(records):
        require(rec.get("frame")==i,"Out-of-order observation")
        for key in ("mask","depth"):
            if rec.get(key) is None:continue
            p=_local(root,rec[key])
            with Image.open(p) as im:
                require(im.size==(width,height),"Vision raster dimension mismatch")
                require(im.mode in ("L","I;16","I"),"Vision raster must be single channel")
        for label in ("pose","hands"):
            val=rec.get(label,[])
            require(isinstance(val,list) and len(val)<=64,"Invalid landmarks")
            for pt in val:
                require(isinstance(pt,dict) and all(k in pt for k in ("x","y","confidence")),"Landmark missing fields")
                require(all(isinstance(pt[k],(int,float)) and math.isfinite(pt[k]) for k in ("x","y","confidence")),"Invalid landmark value")
                require(0<=pt["x"]<=1 and 0<=pt["y"]<=1 and 0<=pt["confidence"]<=1,"Landmark outside bounds")
    return True

def read_observations(path,frames,width,height):
    path=Path(path).resolve();data=json.loads(path.read_text(encoding="utf8"))
    validate_observations(data,path.parent,frames,width,height)
    return data,path.parent

def per_frame_evidence(data,root,index):
    record=data["timeline"][index];out={"pose":record.get("pose",[]),"hands":record.get("hands",[])}
    for key in ("mask","depth"):
        if record.get(key):
            with Image.open(_local(root,record[key])) as image:
                out[key]=image.convert("L").copy()
        else:out[key]=None
    return out

def mediapipe_extract(frames,pose_model,hand_model=None,confidence_floor=.45):
    """Inference on provided RGB PIL frames. Returns actual model estimates only.

    PoseLandmarker uses IMAGE mode, so video temporal smoothing is performed
    downstream, and empty detections are recorded as missing.
    """
    require(0<=confidence_floor<=1,"Invalid confidence")
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import vision,BaseOptions
    except ImportError as exc:
        raise RuntimeError("Install optional mediapipe>=0.10.14 and official model tasks") from exc
    pose_path=Path(pose_model).resolve()
    require(pose_path.is_file(),"Pose task model missing")
    if hand_model is not None:require(Path(hand_model).resolve().is_file(),"Hand task model missing")
    poses=vision.PoseLandmarker.create_from_options(
        vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(pose_path)),
        running_mode=vision.RunningMode.IMAGE,num_poses=1))
    hands=None
    if hand_model is not None:
        hands=vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(Path(hand_model).resolve())),
            running_mode=vision.RunningMode.IMAGE,num_hands=2))
    try:
        result=[]
        for idx,frame in enumerate(frames):
            rgb=np.asarray(frame.convert("RGB"),dtype=np.uint8)
            image=mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(rgb))
            found=poses.detect(image)
            pose=[]
            if found.pose_landmarks:
                pose=[{"x":float(np.clip(p.x,0,1)),"y":float(np.clip(p.y,0,1)),
                       "confidence":float(np.clip(p.visibility if p.visibility is not None else 0,0,1))}
                       for p in found.pose_landmarks[0] if (p.visibility or 0)>=confidence_floor]
            detected_hands=[]
            if hands:
                h=hands.detect(image)
                for hand in h.hand_landmarks:
                    detected_hands.extend([{"x":float(np.clip(p.x,0,1)),"y":float(np.clip(p.y,0,1)),
                        "confidence":1.} for p in hand])
            result.append({"frame":idx,"pose":pose,"hands":detected_hands,
                           "mask":None,"depth":None})
        return {"schema":SCHEMA,"width":frames[0].width,"height":frames[0].height,
                "frames":len(frames),"timeline":result,"depth_estimated":False,
                "segmentation_estimated":False,"model_sources":{
                   "pose_model_sha256":sha256(pose_path),
                   "hand_model_sha256":sha256(hand_model) if hand_model else None}}
    finally:
        poses.close()
        if hands:hands.close()

def anchor_point(record,kind="hands",confidence=.45):
    pts=[p for p in record.get(kind,[]) if p["confidence"]>=confidence]
    if not pts:return None
    x=sum(p["x"] for p in pts)/len(pts);y=sum(p["y"] for p in pts)/len(pts)
    return (float(x),float(y))

def depth_occlusion_mask(subject_mask,depth,threshold=128):
    """Binary foreground proxy; depth scale and direction must be calibrated.

    Never infer scale/sign of monocular depth automatically. Config threshold
    denotes foreground pixels with *lower* calibrated intensity.
    """
    require(subject_mask is not None,"Subject segmentation mask is required")
    a=np.asarray(subject_mask.convert("L"),dtype=np.uint8)
    if depth is None:return Image.fromarray(a,mode="L")
    d=np.asarray(depth.convert("L"),dtype=np.uint8)
    require(a.shape==d.shape,"Depth/mask dimensions differ")
    require(0<=threshold<=255,"Invalid depth threshold")
    return Image.fromarray(np.where(d<=threshold,a,0).astype("uint8"),mode="L")
