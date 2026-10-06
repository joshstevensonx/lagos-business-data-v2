from lagosdata.merge import deduplicate

def test_phone_merge_fills_fields_and_tracks_sources():
    rows=deduplicate([{'name':'A Shop','phone':'+2348031234567','source':'Google Maps'},
                      {'name':'A Shop','phone':'+2348031234567','website':'https://example.org','source':'Finelib'}])
    assert len(rows)==1 and rows[0]['website']=='https://example.org'
    assert rows[0]['source']=='Multiple sources (cross-verified)'
    assert rows[0]['sources_all']==['Google Maps','Finelib']

def test_place_id_is_strongest_and_conflicts_are_audited():
    audit=[]
    rows=deduplicate([{'name':'One','place_id':'id','phone':'+2348031234567','source':'Google Maps'},
                      {'name':'Other label','place_id':'id','phone':'+2348051234567','source':'Places API'}],audit=audit)
    assert len(rows)==1 and rows[0]['phone']=='+2348051234567'
    assert rows[0]['conflicts'] and audit[0]['decision']=='merge'
