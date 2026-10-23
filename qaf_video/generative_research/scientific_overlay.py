"""Typed, provenance-bound wellness claims for cinematic overlays.

P101 implementation slice. Rejects unverified numbers, invalid units and
unsubstantiated clinical claims. This engine never diagnoses or advises.
"""
from __future__ import annotations
import json, math, re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from ..core import require,sha256
SCHEMA="qaf_scientific_overlay_v1"
UNITS={"steps":"pasos","minutes":"min","hours":"h","bpm":"lpm","score":"puntos",
       "count":"registros","percent":"%"}
ALLOW={"user_reported","device_measured","clinician_documented"}
def validate_claims(data):
 require(data.get("schema")==SCHEMA,"Unknown overlay schema")
 items=data.get("claims")
 require(isinstance(items,list) and 1<=len(items)<=24,"Claims required")
 ids=set()
 for row in items:
  key=row.get("id");require(isinstance(key,str) and re.fullmatch(r"[A-Za-z0-9_-]{1,40}",key) and key not in ids,"Invalid claim id")
  ids.add(key)
  value=row.get("value")
  require(type(value) in (int,float) and math.isfinite(value),"Invalid numerical claim")
  require(row.get("unit") in UNITS,"Unknown physical unit")
  require(row.get("evidence_class") in ALLOW,"Undocumented evidence class")
  require(isinstance(row.get("source_record"),str) and len(row["source_record"])>=6,"Source record required")
  require(isinstance(row.get("label"),str) and 1<=len(row["label"])<=64,"Label required")
  require(isinstance(row.get("observed_at"),str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",row["observed_at"]),"Observation date required")
  require(row.get("asserts_diagnosis") is False and row.get("asserts_treatment") is False,
          "Medical claims cannot be inferred by the graphics engine")
 return {"validated":True,"claims":len(items),"ids":sorted(ids)}
def overlay_card(base,claim,left,top):
 require(base.mode in ("RGB","RGBA"),"RGB input expected")
 w,h=base.size
 require(0<=left<w and 0<=top<h,"Overlay origin outside image")
 canvas=base.convert("RGBA")
 label=claim["label"]
 value=f'{claim["value"]:g} {UNITS[claim["unit"]]}'
 card_w=min(420,w-left);card_h=min(92,h-top)
 require(card_w>=135 and card_h>=65,"Insufficient space for card")
 draw=ImageDraw.Draw(canvas,"RGBA")
 draw.rounded_rectangle((left,top,left+card_w,top+card_h),radius=12,fill=(5,35,37,236),outline=(0,200,115,220),width=2)
 font_root=Path(__file__).resolve().parents[1]/"assets/fonts"
 try:
  title_font=ImageFont.truetype(str(font_root/"DejaVuSans.ttf"),14)
  value_font=ImageFont.truetype(str(font_root/"DejaVuSans-Bold.ttf"),22)
 except OSError:
  title_font=ImageFont.load_default();value_font=title_font
 draw.text((left+12,top+10),label,fill=(234,249,240,255),font=title_font)
 draw.text((left+12,top+35),value,fill=(69,240,152,255),font=value_font)
 return canvas.convert("RGB")
def render_overlay(background,claims_manifest,output):
 input_path=Path(background).resolve()
 manifest=Path(claims_manifest).resolve()
 data=json.loads(manifest.read_text(encoding="utf8"))
 validation=validate_claims(data)
 with Image.open(input_path) as raw:image=raw.convert("RGB")
 left=20;top=20
 for claim in data["claims"]:
  image=overlay_card(image,claim,left,top)
  top+=103
  require(top<=image.height+103,"Insufficient room for all cards")
 output=Path(output).resolve();require(output.suffix.lower()==".png","PNG required")
 output.parent.mkdir(parents=True,exist_ok=True);image.save(output)
 return {**validation,"render_sha256":sha256(output),"manifest_sha256":sha256(manifest),
          "clinical_assertions_generated":False,"human_review_required":True}
