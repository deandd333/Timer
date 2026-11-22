import os 
import sys 

import pytest 

sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

@pytest.fixture
def fake_state_file(tmp_path,monkeypatch):
    import state 

    temp_file = tmp_path / 'timer.state'
    monkeypatch.setattr(state,"STATE_FILE",temp_file)
    return temp_file
