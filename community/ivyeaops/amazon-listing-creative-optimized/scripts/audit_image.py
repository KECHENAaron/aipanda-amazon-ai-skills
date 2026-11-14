# AIPANDA public curation, modified 2026-11-14; AGPL-3.0; see PUBLIC_CHANGES.md.
"""Read-only raster checks; semantic and SKU reviews remain human tasks."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image


def audit(path, main=False, ocr=False):
    path=Path(path)
    with Image.open(path) as im:
        width,height=im.size;mode=im.mode;fmt=im.format
        rgb=im.convert('RGB')
        coords=[(x,y) for x in range(width) for y in (0,height-1)]+[(x,y) for y in range(1,height-1) for x in (0,width-1)]
        white=sum(min(rgb.getpixel(p))>=250 for p in coords)/len(coords)
    issues=[]
    if main and white<0.99:issues.append('edge_not_near_white_review_background')
    if max(width,height)<1000:issues.append('below_1000px_zoom_recommendation')
    if fmt not in {'JPEG','PNG','TIFF','GIF'}:issues.append('format_requires_marketplace_check')
    result={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':width,'height':height,'mode':mode,'format':fmt,
        'near_white_edge_fraction':white,'issues':issues,'status':'NEEDS_HUMAN_REVIEW','ocr':{'status':'not_requested'},
        'human_checks_required':['exact_sku_identity','accessory_and_quantity_truth','claim_evidence','category_policy','mobile_readability'],
        'limit':'边缘像素检查不能证明整幅纯白、产品占比或Amazon合规；OCR不能自动确认规格真伪','business_writes':0}
    if ocr:
        runner=shutil.which('swift')
        if not runner:result['ocr']={'status':'unavailable','reason':'swift_not_found'}
        else:
            try:
                p=subprocess.run([runner,str(Path(__file__).with_name('ocr_macos.swift')),str(path.resolve())],capture_output=True,text=True,timeout=60)
                result['ocr']={'status':'ok','lines':json.loads(p.stdout)} if p.returncode==0 else {'status':'failed','reason':p.stderr[-800:]}
            except (subprocess.TimeoutExpired,json.JSONDecodeError) as e:result['ocr']={'status':'failed','reason':type(e).__name__}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image');p.add_argument('--main',action='store_true');p.add_argument('--ocr',action='store_true');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
    if out.exists():raise FileExistsError('输出已存在')
    result=audit(a.image,a.main,a.ocr);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
