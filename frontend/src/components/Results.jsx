import { useState } from 'react';
import { ArrowUpRight, Check, Copy, GitBranch, Layers3, ShieldCheck, Sparkles } from 'lucide-react';

export default function Results({ result }) {
  const [copyStatus, setCopyStatus] = useState('');
  async function copy() {
    try { await navigator.clipboard.writeText(JSON.stringify(result, null, 2)); setCopyStatus('Copied'); }
    catch { setCopyStatus('Copy unavailable. Select the result text to copy it.'); }
  }
  if (!result) return <section className="result-placeholder" aria-label="Your solution blueprint">
    <div className="blueprint-grid"><div className="blueprint-node"><Layers3 size={26}/></div><span className="connector"/><div className="blueprint-node central"><Sparkles size={29}/></div><span className="connector"/><div className="blueprint-node"><GitBranch size={26}/></div></div>
    <span className="eyebrow">FROM CHALLENGE TO CLARITY</span><h2>Your next AI solution<br/>starts with a problem.</h2><p>Describe what’s slowing your business down.<br/>We’ll help you map a practical way forward.</p>
    <div className="preview-features"><span><Check size={15}/> Tailored approach</span><span><Check size={15}/> Architecture & roadmap</span><span><Check size={15}/> Transparent sources</span></div>
    <div className="placeholder-note"><ShieldCheck size={17}/><span>Grounded in public information.<br/>Designed for exploration, with you in control.</span></div>
  </section>;
  return <section className="results" aria-label="Your solution blueprint" aria-live="polite">
    <div className="result-title"><span className="eyebrow"><Sparkles size={14}/> YOUR SOLUTION BLUEPRINT</span><span className="live-tag">{result.fromHistory ? 'Saved AI response' : 'Live AI response'}</span></div>
    <div className="result-actions"><small>{result.created_at ? `Saved ${new Date(result.created_at).toLocaleString()}` : ''}</small><button className="secondary-button" onClick={copy}><Copy size={13}/> Copy result</button></div><p className="copy-status" role="status">{copyStatus}</p>
    <h2>{result.solution_name}</h2><p className="summary">{result.problem_summary}</p>
    <div className="proposal-note"><ShieldCheck size={18}/><p>{result.grounding_note}</p></div>
    <div className="result-section"><h3>Recommended approach <span>Proposed</span></h3><p>{result.recommended_approach}</p></div>
    <div className="result-section"><h3>Why this approach fits</h3><p>{result.reasoning}</p></div>
    <div className="result-section"><h3><GitBranch size={17}/> Architecture <span>Proposed</span></h3><ol className="architecture">{result.architecture_steps.map((step, i) => <li key={i}><span>{String(i + 1).padStart(2, '0')}</span>{step}</li>)}</ol></div>
    <div className="result-section"><h3>Suggested technologies</h3><div className="tech-tags">{result.suggested_technologies.map((tech, i) => <span key={i}>{tech}</span>)}</div></div>
    <div className="result-section"><h3>Implementation roadmap</h3><ol className="roadmap">{result.implementation_roadmap.map((step, i) => <li key={i}><span>{i + 1}</span><p>{step}</p></li>)}</ol></div>
    <div className="benefit-grid"><div><h3>Expected benefits</h3><ul>{result.expected_benefits.map((x, i) => <li key={i}><Check size={15}/><span>{x}</span></li>)}</ul></div><div><h3>Things to consider</h3><ul>{result.considerations.map((x, i) => <li key={i}><span className="small-dot"/><span>{x}</span></li>)}</ul></div></div>
    <div className="result-section oversight"><h3><ShieldCheck size={16}/> Human oversight</h3><p>{result.human_oversight}</p></div>
    <div className="sources"><div className="section-heading"><h3>Knowledge sources</h3><span className="retrieval-tag">{result.retrieval_mode === 'vector' ? 'Semantic vector retrieval' : 'Keyword fallback'}</span></div><p className="source-intro">Curated source summaries, separate from the AI’s proposal. General references describe engineering concepts, not company offerings.</p>{result.source_references.length ? result.source_references.map(source => <a key={source.id} href={source.url} target="_blank" rel="noreferrer"><div><strong>{source.title}</strong><p>{source.description}</p><small>{source.document_type === 'company_reference' ? 'Company reference' : 'General engineering reference'} · Reviewed {source.verified_on}</small><small>{source.chunk_id}</small></div><ArrowUpRight size={19}/></a>) : <p>No useful context found. Treat this as a general technical proposal.</p>}</div>
  </section>;
}
