from ..classify import classify
from ..taxonomy import normalise

def classify_records(records):
    for row in records:
        group,sub=classify(row.get('label',''),row.get('name','')); row['group'],row['sub']=group,sub
        row['legacy18']=row.get('legacy18') or normalise(row.get('label',''),row.get('name',''))
    return records
