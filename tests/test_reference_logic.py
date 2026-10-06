from lagosdata.classify import classify
from lagosdata.normalise import norm_name,norm_addr,is_poi
from lagosdata.taxonomy import normalise
from lagosdata.tree import TREE,ALL_TERMS,ALL_SUBS
from lagosdata.score import score,band

def test_tree_reference_exports():
    assert len(TREE)==29
    assert len(ALL_SUBS)==436
    assert len(ALL_TERMS)==321

def test_ordered_classification_and_legacy_barber():
    assert classify('Pharmacy','Medplus')==('Health & Medical','Pharmacies')
    assert classify('Barber shop','Prince Barbing')==('Beauty & Personal Care','Barbers')
    assert normalise('Barber shop','Prince Barbing')=='Barbers'

def test_normalisers_and_poi():
    assert norm_name('The Lagos Services Ltd')=='lagos'
    assert norm_addr('12 Allen Road, Shop 3')=='12 allen 3'
    assert is_poi({'name':'Roundabout','label':''})
    assert not is_poi({'name':'Bus Stop Pharmacy','label':'Pharmacy'})

def test_score_approved_weights_and_dual_shape():
    rec={'title':'Restaurant','categoryName':'Restaurant','reviewsCount':0,
         'additionalInfo':{'Service options':[{'Delivery':True},{'Takeout':True}]}}
    result,components,category=score(rec,{})
    assert components['Google Delivery flag']==25 and components['Takeout']==5
    assert category=='Restaurant / Food' and band(result).startswith('Cool')
