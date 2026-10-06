import json
from pathlib import Path
from ..workbook.magazine import build_magazine
from ..workbook.delivery import build_delivery

def write_master(run_dir,records):
    path=Path(run_dir)/'master.json'; path.write_text(json.dumps(records,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); return path

def build_report(run_dir,records,config,searches=()):
    write_master(run_dir,records)
    output=Path(run_dir)/config.output.workbook
    if config.pipeline=='magazine': build_magazine(records,config,searches,output)
    else: build_delivery(records,config,output)
    return output
