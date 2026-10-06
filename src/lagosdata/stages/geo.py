from ..areas import nearest_area

def assign_areas(records, areas, core_areas=()):
    for row in records:
        row['area'],row['zone']=nearest_area(row.get('lat',''),row.get('lng',''),areas,row.get('addr',''),core_areas=core_areas)
    return records
