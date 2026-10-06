from lagosdata.areas import nearest_area,derive_centroids

def test_inside_outside_and_missing_coordinate_assignment():
    areas={'Here':{'lat':6.5,'lng':3.3,'radius_km':1.0}}
    assert nearest_area(6.5,3.3,areas,core_areas=['Here'])==('Here','Core catchment')
    assert nearest_area(0,0,areas)==('Outside catchment','Ring area')
    assert nearest_area('', '',areas,'Shop in Here',core_areas=['Here'])==('Here','Core catchment')
    assert nearest_area('', '',areas,'unknown')==('Unassigned','')

def test_centroid_uses_medians_and_marks_low_confidence():
    rows=[{'addr':'Test area','lat':6.5,'lng':3.3},{'addr':'Test area','lat':6.6,'lng':3.4},{'addr':'Test area','lat':6.51,'lng':3.31}]
    result=derive_centroids(rows,['Test area'])['Test area']
    assert result['lat']==6.51 and result['lng']==3.31 and result['confidence']=='review required'
