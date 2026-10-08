import { test, expect } from '@playwright/test';
const examples = [
  { id: 'knowledge', title: 'Find knowledge faster', category: 'Knowledge management', business_problem: 'Our employees need internal document search with references to HR policies.', industry: 'IT Services' },
  { id: 'support', title: 'Support every customer', category: 'Customer experience', business_problem: 'Our customer support team needs help answering repetitive questions with human escalation.', industry: 'Retail' },
  { id: 'documents', title: 'Put documents to work', category: 'Document intelligence', business_problem: 'Our finance team needs scanned invoice document text extraction and review.', industry: 'Finance' },
];
const result = {
  solution_name: 'Enterprise Knowledge Assistant', problem_summary: 'Employees need reliable answers from internal documents.',
  recommended_approach: 'Build a permission-aware document assistant.', reasoning: 'Answers need document context.', human_oversight: 'Review low-confidence responses.', architecture_steps: ['Documents', 'Vector search', 'LLM', 'Application'],
  suggested_technologies: ['FastAPI', 'FAISS'], implementation_roadmap: ['Review permissions', 'Implement search', 'Evaluate answers'],
  expected_benefits: ['Faster search'], considerations: ['Protect access to documents'],
  grounding_note: 'The architecture is an independent proposal.', generation_mode: 'live', retrieval_mode: 'vector',
  source_references: [{ id: 'enterprise-search', title: 'Retrieval and semantic search', url: 'https://docs.langchain.com/oss/python/deepagents/retrieval', description: 'Retrieval supplies relevant context.', verified_on: '2026-10-08', document_type: 'general_reference', chunk_id: 'enterprise-search:0' }],
};
async function mockStatus(page) {
  await page.route('**/health', route => route.fulfill({ json: { status: 'ok', llm_configured: true, retrieval_mode: 'vector' } }));
  await page.route('**/api/examples', route => route.fulfill({ json: examples }));
  await page.route('**/api/knowledge/status', route => route.fulfill({ json: { documents: 8, indexed_chunks: 8, retrieval_mode: 'vector', scope: 'General AI engineering references.' } }));
  await page.route('**/api/history?*', route => route.fulfill({ json: { items: [], total: 0, limit: 6, offset: 0 } }));
}
test('example selection, loading, structured results, and grounded link', async ({ page }) => {
  await mockStatus(page);
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/analyze', async route => { await gate; await route.fulfill({ json: result }); });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Generate AI Solution' })).toBeDisabled();
  await page.getByRole('button', { name: /Find knowledge faster/ }).click();
  await expect(page.getByLabel('Your business challenge')).toHaveValue(examples[0].business_problem);
  await page.getByRole('button', { name: 'Generate AI Solution' }).click();
  await expect(page.locator('.loading-card')).toContainText('Connecting the dots');
  await expect(page.getByLabel('Your business challenge')).toBeDisabled();
  release();
  await expect(page.getByRole('heading', { name: result.solution_name })).toBeVisible();
  await expect(page.getByRole('link', { name: /Retrieval and semantic search/ })).toHaveAttribute('href', result.source_references[0].url);
  await expect(page.getByText('Semantic vector retrieval')).toBeVisible();
});
test('provider errors are visible and retry remains possible', async ({ page }) => {
  await mockStatus(page);
  await page.route('**/api/analyze', route => route.fulfill({ status: 503, json: { detail: 'The AI provider is unavailable. Please try again.' } }));
  await page.goto('/');
  await page.getByRole('button', { name: /Find knowledge faster/ }).click();
  await page.getByRole('button', { name: 'Generate AI Solution' }).click();
  await expect(page.getByRole('alert')).toContainText('AI provider is unavailable');
  await expect(page.getByRole('button', { name: 'Generate AI Solution' })).toBeEnabled();
});
test('mobile layout fits and source fallback is clearly labeled', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockStatus(page);
  await page.route('**/api/analyze', route => route.fulfill({ json: { ...result, retrieval_mode: 'keyword_fallback' } }));
  await page.goto('/');
  await page.getByRole('button', { name: /Find knowledge faster/ }).click();
  await page.getByRole('button', { name: 'Generate AI Solution' }).click();
  await expect(page.getByText('Keyword fallback')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/mobile.png', fullPage: true });
});
test('desktop empty state and help panel', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await mockStatus(page);
  await page.goto('/');
  await expect(page.getByText('Your next AI solution')).toBeVisible();
  await page.screenshot({ path: 'test-results/desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'How it works' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
});
test('live browser-to-backend integration across three sample problems', async ({ page }) => {
  test.skip(process.env.RUN_LIVE_E2E !== '1', 'Requires a running backend and configured Groq key');
  test.setTimeout(240000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('/');
  await expect(page.getByText('AI configured')).toBeVisible({ timeout: 20000 });
  for (const title of ['Find knowledge faster', 'Support every customer', 'Put documents to work']) {
    await page.getByRole('button', { name: new RegExp(title) }).click();
    await page.getByRole('button', { name: 'Generate AI Solution' }).click();
    await expect(page.getByText('Live AI response')).toBeVisible({ timeout: 75000 });
    await expect(page.getByText('Semantic vector retrieval')).toBeVisible();
    await expect(page.locator('.sources a').first()).toHaveAttribute('href', /^https:\/\//);
    await expect(page.locator('.history-grid button').first()).toBeVisible();
  }
  await page.locator('.history-grid button').last().click();
  await expect(page.getByText('Saved AI response')).toBeVisible();
  await page.screenshot({ path: 'test-results/live-result.png', fullPage: true });
  expect(errors).toEqual([]);
});

test('SQL history navigation restores saved recommendations and copying works', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await mockStatus(page);
  const item = { id: 'saved-1', problem: examples[0].business_problem, solution_name: result.solution_name, industry: 'IT Services', created_at: '2026-10-08T05:00:00Z', status: 'completed' };
  await page.route('**/api/history?*', route => route.fulfill({ json: { items: [item], total: 1, limit: 6, offset: 0 } }));
  await page.route('**/api/history/saved-1', route => route.fulfill({ json: { ...item, recommendation: result } }));
  await page.goto('/');
  await page.getByRole('button', { name: /Enterprise Knowledge Assistant/ }).click();
  await expect(page.getByText('Saved AI response')).toBeVisible();
  await expect(page.getByLabel('Your business challenge')).toHaveValue(item.problem);
  await page.getByRole('button', { name: 'Copy result' }).click();
  await expect(page.getByText('Copied', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(result.solution_name);
});
