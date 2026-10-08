import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError, SecretStr
from app.config import settings, BASE_DIR
from app.main import create_app
from app.schemas import Recommendation
from app.services.rag_service import Retriever, INDEX_PATH
from app.services import recommendation_service, llm_service

@pytest.fixture
def recommendation():
    return Recommendation(solution_name="Knowledge assistant", problem_summary="Staff need reliable document search.",
        recommended_approach="Build a permission-aware retrieval assistant with citations and human evaluation.",
        reasoning="The task needs answers grounded in internal documents.", human_oversight="Review uncertain answers and permission changes.",
        architecture_steps=["Documents", "Vector search", "LLM", "Application"],
        suggested_technologies=["Python", "FastAPI", "FAISS"],
        implementation_roadmap=["Audit data and permissions", "Implement retrieval and citations", "Evaluate with representative questions"],
        expected_benefits=["Less time spent searching"], considerations=["Enforce document permissions"])

@pytest.fixture
def client():
    with TestClient(create_app(Retriever(initialize_vector=False), database_url='sqlite:///:memory:')) as test_client:
        test_client.headers['X-Session-ID'] = str(uuid4())
        yield test_client

def test_health_and_examples(client):
    health = client.get('/health').json()
    assert health['status'] == 'ok'
    assert health['retrieval_mode'] == 'keyword_fallback'
    assert health['knowledge_documents'] == 8
    assert health['database'] == 'ok'
    assert 'key' not in health
    assert len(client.get('/api/examples').json()) == 4

@pytest.mark.parametrize('payload', [{}, {'business_problem': 'short'}, {'business_problem': ' ' * 30},
    {'business_problem': 'x' * 4001}, {'business_problem': 'A useful business problem here', 'industry': 'invalid'},
    {'business_problem': 'A useful business problem here', 'extra': 'disallowed'}])
def test_request_validation(client, payload):
    assert client.post('/api/analyze', json=payload).status_code == 422

def test_schema_rejects_invalid_output(recommendation):
    payload = recommendation.model_dump()
    payload['architecture_steps'] = []
    with pytest.raises(ValidationError):
        Recommendation.model_validate(payload)

def test_keyword_retrieval_and_unrelated():
    retriever = Retriever(initialize_vector=False)
    docs, mode = retriever.search('internal document search employee knowledge')
    assert docs[0]['id'] == 'enterprise-search'
    assert mode == 'keyword_fallback'
    assert retriever.search('volcanoes tectonic magma planets')[0] == []

def test_vector_initialization_failure_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr('app.services.rag_service.INDEX_PATH', tmp_path)
    retriever = Retriever()
    assert retriever.mode == 'keyword_fallback'
    assert retriever.search('customer support')[0]

def test_success_and_trusted_sources(client, monkeypatch, recommendation):
    fake = AsyncMock(return_value=recommendation)
    monkeypatch.setattr(recommendation_service, 'generate', fake)
    response = client.post('/api/analyze', json={'business_problem': 'Employees need internal document search and HR policy answers.'})
    assert response.status_code == 200
    body = response.json()
    assert body['generation_mode'] == 'live'
    retrieved = fake.call_args.args[2]
    assert [s['id'] for s in body['source_references']] == [d['id'] for d in retrieved]
    for source in body['source_references']:
        doc = next(d for d in retrieved if d['id'] == source['id'])
        assert source['url'] == doc['url']
        assert source['description'] == doc['description']

def test_no_sources_general_proposal(client, monkeypatch, recommendation):
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    body = client.post('/api/analyze', json={'business_problem': 'Volcanoes tectonic magma planetary geology'}).json()
    assert body['source_references'] == []
    assert 'general technical proposal' in body['grounding_note']

def test_missing_key(client, monkeypatch):
    monkeypatch.setattr(settings, 'groq_api_key', SecretStr(''))
    response = client.post('/api/analyze', json={'business_problem': 'Employees need internal document search.'})
    assert response.status_code == 503
    assert 'GROQ_API_KEY' in response.json()['detail']

def test_provider_failure_safe(client, monkeypatch):
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(side_effect=llm_service.AIUnavailable('Provider unavailable')))
    response = client.post('/api/analyze', json={'business_problem': 'Employees need internal document search.'})
    assert response.status_code == 503

def test_unexpected_failure_safe(client, monkeypatch):
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(side_effect=RuntimeError('private-detail')))
    response = client.post('/api/analyze', json={'business_problem': 'Employees need internal document search.'})
    assert response.status_code == 500
    assert 'private-detail' not in response.text

def test_bounded_validation_retry(recommendation):
    client = MagicMock()
    invoke = AsyncMock(side_effect=[ValueError('invalid'), recommendation])
    client.with_structured_output.return_value.ainvoke = invoke
    result = asyncio.run(llm_service.generate('business problem', None, [], client=client))
    assert result == recommendation
    assert invoke.await_count == 2

def test_validation_retry_exhaustion():
    client = MagicMock()
    invoke = AsyncMock(side_effect=ValueError('private response'))
    client.with_structured_output.return_value.ainvoke = invoke
    with pytest.raises(llm_service.AIUnavailable, match='validated'):
        asyncio.run(llm_service.generate('problem', None, [], client=client))
    assert invoke.await_count == 2

def test_provider_timeout_no_retry():
    client = MagicMock()
    invoke = AsyncMock(side_effect=TimeoutError('private'))
    client.with_structured_output.return_value.ainvoke = invoke
    with pytest.raises(llm_service.AIUnavailable, match='timed out'):
        asyncio.run(llm_service.generate('problem', None, [], client=client))
    assert invoke.await_count == 1

@pytest.mark.parametrize('model,method', [('openai/gpt-oss-20b', 'json_schema'), ('another-json-model', 'json_mode')])
def test_output_mode_matches_model(monkeypatch, recommendation, model, method):
    monkeypatch.setattr(settings, 'groq_model', model)
    client = MagicMock()
    client.with_structured_output.return_value.ainvoke = AsyncMock(return_value=recommendation)
    asyncio.run(llm_service.generate('business problem', None, [], client=client))
    assert client.with_structured_output.call_args.kwargs['method'] == method
    if method == 'json_schema':
        assert client.with_structured_output.call_args.kwargs['strict'] is True

def test_cors(client):
    response = client.options('/api/analyze', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST'})
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
    response = client.options('/api/analyze', headers={'Origin': 'https://untrusted.example', 'Access-Control-Request-Method': 'POST'})
    assert 'access-control-allow-origin' not in response.headers

def test_body_size_limit(client):
    assert client.post('/api/analyze', content=b'x' * 20001).status_code == 413
    assert client.post('/api/analyze', content=iter([b'x' * 10000, b'x' * 10001])).status_code == 413

def test_shared_budget(client, monkeypatch, recommendation):
    monkeypatch.setattr(settings, 'rate_limit_per_minute', 1)
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    payload = {'business_problem': 'Employees need internal document search.'}
    assert client.post('/api/analyze', json=payload).status_code == 200
    response = client.post('/api/analyze', json=payload)
    assert response.status_code == 429
    assert response.headers['Retry-After'] == '60'

@pytest.mark.vector
@pytest.mark.skipif(not (INDEX_PATH / 'metadata.json').exists(), reason='Build the vector index first')
def test_real_vector_retrieval():
    retriever = Retriever()
    assert retriever.mode == 'vector'
    examples = json.loads((BASE_DIR / 'app/data/examples.json').read_text())
    expected = ['enterprise-search', 'customer-support', 'document-processing', 'workflow-automation']
    for example, doc_id in zip(examples, expected):
        docs, mode = retriever.search(example['business_problem'])
        assert mode == 'vector'
        assert doc_id in [d['id'] for d in docs]
    assert retriever.search('Explain the orbital mechanics of neutron stars and black holes.')[0] == []
    docs, _ = retriever.search('Predict next month retail product demand from historical weekly sales and inventory.')
    assert docs[0]['id'] == 'predictive-analytics'

def test_problem_contract_sql_history_and_isolation(client, monkeypatch, recommendation):
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    problem = 'Employees need faster internal document search.'
    response = client.post('/api/analyze', json={'problem': problem})
    assert response.status_code == 200
    saved = response.json()
    assert saved['analysis_id']
    listing = client.get('/api/history').json()
    assert listing['total'] == 1
    assert listing['items'][0]['problem'] == problem
    assert listing['items'][0]['status'] == 'completed'
    detail = client.get('/api/history/' + saved['analysis_id']).json()
    assert detail['recommendation']['solution_name'] == recommendation.solution_name
    assert detail['created_at'].endswith('Z')
    assert client.get('/api/history', headers={'X-Session-ID': str(uuid4())}).json()['total'] == 0
    assert client.get('/api/history/' + saved['analysis_id'], headers={'X-Session-ID': str(uuid4())}).status_code == 404

def test_history_validation(client):
    assert client.get('/api/history?limit=100').status_code == 422
    assert client.get('/api/history?offset=-1').status_code == 422
    assert client.get('/api/history/not-a-uuid').status_code == 422
    assert client.get('/api/history', headers={'X-Session-ID': 'bad'}).status_code == 422
    client.headers.pop('X-Session-ID')
    assert client.get('/api/history').status_code == 400

def test_no_history_saved_on_provider_failure(client, monkeypatch):
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(side_effect=llm_service.AIUnavailable('Unavailable')))
    assert client.post('/api/analyze', json={'problem': 'Employees need internal document search.'}).status_code == 503
    assert client.get('/api/history').json()['total'] == 0

def test_database_persists_across_app_restart(tmp_path, monkeypatch, recommendation):
    url = 'sqlite:///' + (tmp_path / 'history.db').as_posix()
    token = str(uuid4())
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    with TestClient(create_app(Retriever(False), url)) as first:
        response = first.post('/api/analyze', json={'problem': 'Employees need internal document search.'}, headers={'X-Session-ID': token})
        assert response.status_code == 200
    with TestClient(create_app(Retriever(False), url)) as second:
        assert second.get('/api/history', headers={'X-Session-ID': token}).json()['total'] == 1

def test_database_error_is_safe(client, monkeypatch, recommendation):
    from sqlalchemy.exc import OperationalError
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    def broken(*args):
        raise OperationalError('private sql', {}, Exception('private path'))
    monkeypatch.setattr(client.app.state.history, 'save', broken)
    response = client.post('/api/analyze', json={'problem': 'Employees need internal document search.'})
    assert response.status_code == 503
    assert 'private' not in response.text

def test_knowledge_status(client):
    status = client.get('/api/knowledge/status').json()
    assert status['documents'] == 8
    assert status['company_documents'] == 0
    assert status['company_identity_verified'] is False

def test_new_api_returns_session_token(client, monkeypatch, recommendation):
    client.headers.pop('X-Session-ID')
    monkeypatch.setattr(recommendation_service, 'generate', AsyncMock(return_value=recommendation))
    response = client.post('/api/analyze', json={'problem': 'Employees need internal document search.'})
    token = response.headers['X-Session-ID']
    assert client.get('/api/history', headers={'X-Session-ID': token}).json()['total'] == 1
