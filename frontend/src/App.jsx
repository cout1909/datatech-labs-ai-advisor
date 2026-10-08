import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, CircleHelp, FileText, GitBranch, Layers3, LoaderCircle, MessageSquare, RotateCcw, ShieldCheck, Sparkles, Workflow, X } from 'lucide-react';
import { api } from './api';
import Results from './components/Results';
import History from './components/History';

const icons = [BookOpen, MessageSquare, FileText, Workflow];
export default function App() {
  const [problem, setProblem] = useState('');
  const [industry, setIndustry] = useState('');
  const [examples, setExamples] = useState([]);
  const [health, setHealth] = useState(null);
  const [statusError, setStatusError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [help, setHelp] = useState(false);
  const [historyRevision, setHistoryRevision] = useState(0);
  const [knowledge, setKnowledge] = useState(null);
  const inputRef = useRef(null);
  const resultsRef = useRef(null);
  async function loadStatus() {
    setStatusError(false);
    try { setHealth(await api('/health')); } catch { setStatusError(true); }
    try { setExamples(await api('/api/examples')); } catch { /* Status panel gives retry. */ }
    try { setKnowledge(await api('/api/knowledge/status')); } catch { /* Status can be retried. */ }
  }
  useEffect(() => { loadStatus(); }, []);
  async function submit(event) {
    event.preventDefault();
    if (loading) return;
    if (problem.trim().length < 20) { setError('Please describe your challenge in at least 20 characters.'); inputRef.current?.focus(); return; }
    setError(''); setResult(null); setLoading(true);
    try {
      const data = await api('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ problem: problem.trim(), industry: industry || null }) });
      setResult(data); setHistoryRevision(value => value + 1);
      requestAnimationFrame(() => { resultsRef.current?.focus({ preventScroll: true }); resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  const ready = health?.llm_configured && !statusError;
  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="#"><span className="brand-mark"><Layers3 size={23}/></span><span>DataTech Labs<span className="brand-sub">AI PROJECT ADVISOR</span></span></a><span className="portfolio-label">INDEPENDENT DEMO</span><div className="nav-label">WORKSPACE</div><a className="nav-item active" href="#advisor"><Sparkles size={18}/> Project advisor <span className="nav-indicator"/></a><a className="nav-item" href="#examples"><BookOpen size={18}/> Example use cases <ArrowUpRight size={14}/></a><a className="nav-item" href="#history"><Layers3 size={18}/> Previous analyses</a><button className="nav-item" onClick={() => setHelp(true)}><CircleHelp size={18}/> How it works</button><div className="sidebar-bottom"><div className="stack-visual"><span/><span/><span/></div><h3>Ideas into impact.</h3><p>A practical starting point for your next AI initiative.</p><div className="built-with"><span className="small-dot"/> FastAPI · React · RAG</div></div><div className="sidebar-footer"><span className="avatar">AI</span><div>Engineering portfolio<small>Explore. Build. Learn.</small></div></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>Project advisor</strong></div><div className={`system-status ${ready ? 'ready' : ''}`}><span/>{statusError ? 'Backend offline' : !health ? 'Connecting…' : ready ? 'AI configured' : 'API key needed'}</div></header>
    <main id="advisor"><div className="page-heading"><div><span className="eyebrow"><span className="tiny-line"/> AI, WITH A BUSINESS PURPOSE</span><p className="product-name">DataTech Labs AI Project Advisor</p><h1>From Business Challenges<br className="mobile-break"/> to AI Solutions</h1><p>Turn business challenges into practical AI solution plans.</p></div><div className="heading-badge"><ShieldCheck size={17}/> Source-aware recommendations</div></div>
      <div className="disclaimer"><ShieldCheck size={16}/><span>Independent demonstration project. Not affiliated with or endorsed by DataTech Labs.</span></div>
      <div className="workspace-grid"><div className="input-column"><section className="input-card"><div className="card-heading"><span className="step-label">01</span><div><h2>Describe your business challenge</h2><p>Start with a challenge. We’ll connect the dots.</p></div></div><form onSubmit={submit}><label htmlFor="problem">Your business challenge <span>*</span></label><textarea ref={inputRef} id="problem" value={problem} onChange={e => setProblem(e.target.value)} maxLength={4000} disabled={loading} placeholder="Our team spends too much time searching internal documents. We need a faster way to find reliable answers…" aria-describedby="input-hint"/><div id="input-hint" className="input-hint"><span>Include your process, pain points, and desired outcome.</span><span>{problem.length.toLocaleString()} / 4,000</span></div><label htmlFor="industry">Industry <span className="optional">Optional</span></label><div className="select-wrap"><select id="industry" value={industry} disabled={loading} onChange={e => setIndustry(e.target.value)}><option value="">Select an industry</option>{['Finance', 'Healthcare', 'Retail', 'Manufacturing', 'IT Services', 'Other'].map(x => <option key={x}>{x}</option>)}</select><ChevronDown size={16}/></div><button className="analyze-button" disabled={loading || problem.trim().length < 20} type="submit">{loading ? <><LoaderCircle className="spin" size={18}/> Analyzing your challenge…</> : <><Sparkles size={18}/> Generate AI Solution <ArrowRight size={18}/></>}</button><p className="privacy-note">Your challenge is sent to Groq and saved in SQL history. Avoid sharing personal or confidential information.</p>{error && <div role="alert" className="error-message">{error}</div>}{(statusError || (health && !health.llm_configured)) && <div className="setup-note">{statusError ? 'The backend may be starting. Recheck its status before analyzing.' : 'Live AI needs a backend API key. Configure GROQ_API_KEY to enable generation.'}<button type="button" onClick={loadStatus}><RotateCcw size={13}/> Recheck status</button></div>}</form></section>
      <section id="examples" className="examples"><div className="section-heading"><h3>Need a little inspiration?</h3><span>Try an example</span></div><div className="examples-grid">{examples.map((example, i) => { const Icon = icons[i % icons.length]; return <button key={example.id} disabled={loading} onClick={() => { setProblem(example.business_problem); setIndustry(example.industry); setError(''); inputRef.current?.focus(); }}><Icon size={20}/><ArrowUpRight className="example-arrow" size={15}/><strong>{example.title}</strong><span>{example.category}</span></button>; })}</div></section><div className="process-caption"><span>RETRIEVE</span><i/><span>REASON</span><i/><span>RECOMMEND</span></div></div>
      <div className="output-column" ref={resultsRef} tabIndex={-1}><div className="output-heading"><span className="step-label">02</span><h2>Your solution blueprint</h2><span className="output-label">{loading ? 'Working on it' : result ? 'Ready to explore' : 'Awaiting your challenge'}</span></div>{loading ? <section className="loading-card" role="status"><div className="loading-orbit"><Sparkles size={28}/></div><h2>Connecting the dots</h2><p>Finding relevant sources and designing<br/>your proposed solution.</p><span><LoaderCircle className="spin" size={14}/> This can take up to a minute</span></section> : <Results result={result}/>}</div></div>
      <History revision={historyRevision} disabled={loading} onSelect={record => {
        setProblem(record.problem); setIndustry(record.industry || ''); setError('');
        setResult({ ...record.recommendation, analysis_id: record.id, created_at: record.created_at, fromHistory: true });
        requestAnimationFrame(() => { resultsRef.current?.focus({ preventScroll: true }); resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
      }}/>
      <section className="technical-info"><div><Layers3 size={20}/><div><h3>Full-stack AI, thoughtfully connected.</h3><p>React / FastAPI / Groq / Pydantic / SQLAlchemy / SQLite / ONNX embeddings / FAISS</p></div></div><p>{knowledge ? `${knowledge.documents} knowledge documents / ${knowledge.indexed_chunks} indexed chunks / ${knowledge.retrieval_mode === 'vector' ? 'Semantic retrieval ready' : 'Keyword fallback active'}` : 'Knowledge status is unavailable. Recheck the backend connection.'}</p><small>{knowledge?.scope || 'General AI engineering demonstration. No company-specific offerings are claimed.'}</small></section>
      <footer><span>Built as an independent AI engineering portfolio project.</span><span>Thoughtfully built. Transparently sourced.</span></footer>
    </main></div>
    {help && <div className="modal-backdrop" onClick={() => setHelp(false)}><section className="help-modal" role="dialog" aria-modal="true" aria-label="How it works" onClick={e => e.stopPropagation()} onKeyDown={e => { if (e.key === 'Escape') setHelp(false); if (e.key === 'Tab') e.preventDefault(); }}><button autoFocus className="close-button" aria-label="Close how it works" onClick={() => setHelp(false)}><X size={20}/></button><span className="eyebrow">A TRANSPARENT PROCESS</span><h2>From your challenge to a plan.</h2>{[[BookOpen, 'Retrieve', 'Local semantic embeddings and FAISS find related curated engineering references. If unavailable, a labeled keyword search is used.'], [Sparkles, 'Reason', 'Groq receives your challenge and retrieved context. Its structured response is validated before you see it.'], [GitBranch, 'Recommend', 'Explore a proposed architecture, roadmap, and considerations. Source summaries remain separate from the AI proposal.']].map(([Icon, title, text]) => <div className="help-step" key={title}><Icon size={21}/><div><h3>{title}</h3><p>{text}</p></div></div>)}<p className="help-footer"><Check size={16}/> AI proposals need review and are not DataTech Labs commitments.</p></section></div>}
  </div>;
}
