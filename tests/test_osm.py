from lagosdata.sources.osm import parse_elements,build_query

def test_osm_node_way_parse_and_classification():
    result=parse_elements({'elements':[{'type':'node','id':1,'lat':6.5,'lon':3.3,'tags':{'name':'Health Shop','shop':'chemist','phone':'0803 123 4567','website':'https://example.org'}},
        {'type':'way','id':2,'center':{'lat':6.51,'lon':3.31},'tags':{'name':'No phone store','shop':'supermarket'}},
        {'type':'node','id':3,'tags':{'shop':'bakery'}}]})
    assert len(result)==2 and result[0]['phone']=='+2348031234567'
    assert result[0]['group']=='Health & Medical' and result[1]['lat']==6.51
    assert 'out center tags' in build_query(1,2,3,4)
