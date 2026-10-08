import { useEffect, useState } from 'react';
import { ArrowUpRight, Clock3, LoaderCircle, RotateCcw } from 'lucide-react';
import { api } from '../api';

export default function History({ revision, onSelect, disabled }) {
  const [data, setData] = useState({ items: [], total: 0 });
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  async function refresh() {
    setLoading(true); setError('');
    try { setData(await api(`/api/history?limit=6&offset=${offset}`)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, [offset, revision]);
  async function open(id) {
    setSelected(id); setError('');
    try { onSelect(await api(`/api/history/${id}`)); }
    catch (e) { setError(e.message); }
    finally { setSelected(null); }
  }
  return <section className="history-section" id="history" aria-label="Previous analyses">
    <div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE MEMORY</span><h2><Clock3 size={20}/> Previous analyses</h2></div><button className="secondary-button" onClick={refresh} disabled={loading}><RotateCcw size={14}/> Refresh</button></div>
    <p className="history-note">Saved in the backend SQL database for this browser’s anonymous session. Clearing browser storage loses access. Free hosting may reset saved history.</p>
    {error && <p role="alert" className="error-message">{error}</p>}
    {loading ? <p role="status" className="history-empty"><LoaderCircle size={16} className="spin"/> Loading saved analyses…</p> : data.items.length ? <div className="history-grid">{data.items.map(item => <button key={item.id} disabled={disabled || selected !== null} onClick={() => open(item.id)}><div><span>{new Date(item.created_at).toLocaleString()}</span>{selected === item.id ? <LoaderCircle size={15} className="spin"/> : <ArrowUpRight size={16}/>}</div><h3>{item.solution_name}</h3><p>{item.problem}</p><small>Completed · {item.industry || 'General'}</small></button>)}</div> : !error && <p className="history-empty">Your completed analyses will appear here. Generate your first solution to get started.</p>}
    {data.total > 6 && <div className="history-pagination"><button className="secondary-button" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - 6))}>Previous</button><span>{offset + 1}–{Math.min(offset + 6, data.total)} of {data.total}</span><button className="secondary-button" disabled={offset + 6 >= data.total || loading} onClick={() => setOffset(offset + 6)}>Next</button></div>}
  </section>;
}
