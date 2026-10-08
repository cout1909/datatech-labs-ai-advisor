"""Read-only deployment checks. Run with real URLs after authorized deployment."""
import argparse
import httpx

parser = argparse.ArgumentParser()
parser.add_argument('--backend', required=True)
parser.add_argument('--frontend', required=True)
args = parser.parse_args()
backend = args.backend.rstrip('/')
frontend = args.frontend.rstrip('/')
with httpx.Client(timeout=90, follow_redirects=True) as client:
    page = client.get(frontend)
    page.raise_for_status()
    assert 'DataTech Labs AI Project Advisor' in page.text, 'Unexpected frontend title'
    health = client.get(backend + '/health')
    health.raise_for_status()
    assert health.json()['llm_configured'], 'Backend key is not configured'
    assert health.json()['retrieval_mode'] == 'vector', 'Semantic retrieval is not active'
    knowledge = client.get(backend + '/api/knowledge/status')
    knowledge.raise_for_status()
    assert knowledge.json()['indexed_chunks'] > 0
    client.get(backend + '/docs').raise_for_status()
    preflight = client.options(backend + '/api/analyze', headers={
        'Origin': frontend, 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type,x-session-id'})
    preflight.raise_for_status()
    assert preflight.headers.get('access-control-allow-origin') == frontend, 'CORS origin does not match'
print('Frontend, backend, Swagger, vector status and CORS passed. Live generation/history must still be checked in the browser.')
