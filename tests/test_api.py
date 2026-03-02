from fastapi.testclient import TestClient

from server.app import app
from shared.replay import compress_replay


def test_runs_and_leaderboard():
    client = TestClient(app)
    replay = compress_replay([{"left": False, "right": True, "jump_pressed": False, "jump_held": False}])
    payload = {
        "level_id": "level_01",
        "player_name": "qa",
        "best_time_ms": 1234,
        "deaths": 2,
        "seed": 42,
        "replay_data": replay,
    }
    post = client.post('/runs', json=payload)
    assert post.status_code == 200
    lb = client.get('/leaderboard/level_01')
    assert lb.status_code == 200
    assert len(lb.json()) >= 1
