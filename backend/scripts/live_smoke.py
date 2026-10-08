"""Explicit live check: sends only the public sample problems to Groq."""
import json
import sys
import time
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import SavedAnalysis

with TestClient(app) as client:
    client.headers['X-Session-ID'] = str(uuid4())
    print('Health:', client.get('/health').json())
    examples = client.get('/api/examples').json()
    for example in examples[:3]:
        started = time.monotonic()
        response = client.post('/api/analyze', json={k: example[k] for k in ('business_problem', 'industry')})
        if response.status_code != 200:
            print(example['id'], response.status_code, response.json())
            raise SystemExit(1)
        validated = SavedAnalysis.model_validate(response.json())
        assert validated.retrieval_mode == 'vector'
        detail = client.get('/api/history/' + validated.analysis_id)
        assert detail.status_code == 200
        assert detail.json()['recommendation']['solution_name'] == validated.solution_name
        print(json.dumps({'example': example['id'], 'solution': validated.solution_name,
                          'retrieval_mode': validated.retrieval_mode,
                          'sources': [s.id for s in validated.source_references],
                          'seconds': round(time.monotonic() - started, 2)}))
    assert client.get('/api/history').json()['total'] == 3
print('Three live analyses and SQL history checks passed.')
