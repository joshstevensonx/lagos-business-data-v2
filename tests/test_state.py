from lagosdata.state import RunState,append_raw
import json

def test_search_resume_and_raw_append(tmp_path):
    state=RunState(tmp_path/'state.sqlite3')
    assert state.should_run('osm','pharmacy','Ilupeju')
    state.start('osm','pharmacy','Ilupeju');state.finish('osm','pharmacy','Ilupeju','done',3,2)
    assert not state.should_run('osm','pharmacy','Ilupeju')
    assert state.should_run('osm','pharmacy','Ilupeju',force=True)
    state.close()
    raw=append_raw(tmp_path,'osm',[{'name':'A'}]);append_raw(tmp_path,'osm',[{'name':'B'}])
    assert [json.loads(x)['name'] for x in raw.read_text().splitlines()]==['A','B']
