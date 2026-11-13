import { useState, useRef } from "react";
import {
  C, API_URL, PIPELINE_STEPS, ARCH, RULES, BANNED_TAGS, LANG_FLAGS, INDIAN_STATES,
  vc, vbd, vbg, ac, abg, smc,
} from "../constants";
import { Panel, PTitle, CheckCard, SimCard, LoadStep } from "../components/SharedUI";

// ─── Similarity Network Graph ─────────────────────────────────────────────────
function SimilarityGraph({ nodes, edges }) {
  const svgRef = useRef(null);
  const W = 560, H = 340, CX = W/2, CY = H/2;
  if (!nodes || nodes.length === 0) return null;

  const query = nodes.find(n => n.type === "query");
  const others = nodes.filter(n => n.type !== "query");
  const count = others.length;

  const inner = others.slice(0, Math.min(7, count));
  const outer = others.slice(7);
  const positions = { "query": { x: CX, y: CY } };
  inner.forEach((n, i) => {
    const angle = (i / inner.length) * 2 * Math.PI - Math.PI/2;
    const r = 110;
    positions[n.id] = { x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle) };
  });
  outer.forEach((n, i) => {
    const angle = (i / outer.length) * 2 * Math.PI - Math.PI/2 + 0.2;
    const r = 160;
    positions[n.id] = { x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle) };
  });

  return (
    <div style={{background:C.surf2,border:`1px solid ${C.border}`,padding:"4px",marginBottom:16,overflow:"hidden"}}>
      <PTitle>Similarity Network Graph</PTitle>
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto",display:"block"}}>
        <defs>
          <radialGradient id="qGrad" cx="50%" cy="50%">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.4"/>
            <stop offset="100%" stopColor={C.accent} stopOpacity="0.05"/>
          </radialGradient>
        </defs>
        {edges.map((e, i) => {
          const sp = positions[e.source], tp = positions[e.target];
          if (!sp || !tp) return null;
          const col = e.weight >= 80 ? C.red : e.weight >= 55 ? C.yellow : C.accent3;
          const opacity = 0.2 + (e.weight / 100) * 0.6;
          return (
            <line key={i} x1={sp.x} y1={sp.y} x2={tp.x} y2={tp.y}
              stroke={col} strokeWidth={e.weight >= 80 ? 2 : 1} strokeOpacity={opacity}
              strokeDasharray={e.weight < 55 ? "3 3" : "none"}
            />
          );
        })}
        {others.map((n) => {
          const p = positions[n.id];
          if (!p) return null;
          const col = smc(n.score);
          const r = n.score >= 70 ? 7 : 5;
          const label = n.label.length > 18 ? n.label.slice(0, 16) + "…" : n.label;
          const isAbove = p.y < CY;
          return (
            <g key={n.id}>
              <circle cx={p.x} cy={p.y} r={r+4} fill={col} fillOpacity="0.08"/>
              <circle cx={p.x} cy={p.y} r={r} fill={col} fillOpacity="0.7" stroke={col} strokeWidth="1.5"/>
              <text x={p.x} y={isAbove ? p.y - r - 5 : p.y + r + 12}
                textAnchor="middle" fill={C.muted} fontSize="8" fontFamily="'Space Mono',monospace">
                {label}
              </text>
              <text x={p.x} y={isAbove ? p.y - r - 14 : p.y + r + 21}
                textAnchor="middle" fill={col} fontSize="8" fontFamily="'Space Mono',monospace" fontWeight="700">
                {n.score}%
              </text>
            </g>
          );
        })}
        <circle cx={CX} cy={CY} r={28} fill="url(#qGrad)"/>
        <circle cx={CX} cy={CY} r={18} fill={C.accent} fillOpacity="0.15" stroke={C.accent} strokeWidth="2"/>
        <text x={CX} y={CY-4} textAnchor="middle" fill={C.accent}
          fontSize="9" fontFamily="'Syne',sans-serif" fontWeight="800">
          {(query?.label||"").slice(0,14)}
        </text>
        <text x={CX} y={CY+8} textAnchor="middle" fill={C.accent} fontSize="7"
          fontFamily="'Space Mono',monospace">QUERY</text>
        {[{c:C.red,l:"High conflict (≥80%)"},{c:C.yellow,l:"Review (55-79%)"},{c:C.accent3,l:"Low similarity (<55%)"}].map((lg,i)=>(
          <g key={i} transform={`translate(12,${H-50+i*14})`}>
            <circle r="4" fill={lg.c} fillOpacity="0.7"/>
            <text x="10" y="4" fill={C.dim} fontSize="8" fontFamily="'Space Mono',monospace">{lg.l}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

// ─── Language Badge ────────────────────────────────────────────────────────────
function LangBadge({ langDetected }) {
  if (!langDetected || !langDetected.code) return null;
  const flag = LANG_FLAGS[langDetected.code] || "🌐";
  return (
    <div style={{display:"inline-flex",alignItems:"center",gap:6,background:C.surf2,
      border:`1px solid ${C.border}`,padding:"4px 10px",fontSize:10,
      fontFamily:"'Space Mono',monospace",color:C.muted,marginTop:8}}>
      <span>{flag}</span>
      <span style={{color:C.accent}}>{langDetected.label}</span>
      <span style={{color:C.dim}}>·</span>
      <span>{Math.round(langDetected.confidence * 100)}% confident</span>
      <span style={{color:C.dim}}>·</span>
      <span style={{color:C.dim}}>{langDetected.method}</span>
    </div>
  );
}

// ─── Suggestions Panel ─────────────────────────────────────────────────────────
function SuggestionsPanel({ suggestions, onPick }) {
  if (!suggestions || suggestions.length === 0) return null;
  return (
    <div style={{marginTop:14,padding:"14px 16px",background:"rgba(232,255,71,0.04)",
      border:`1px solid rgba(232,255,71,0.15)`}}>
      <PTitle>Title Suggestions</PTitle>
      <div style={{fontSize:11,color:C.muted,marginBottom:10}}>
        These alternatives are unique and unregistered — click to try one:
      </div>
      <div style={{display:"flex",flexWrap:"wrap",gap:7}}>
        {suggestions.map((s,i) => (
          <button key={i} onClick={() => onPick(s)}
            style={{background:C.surf2,border:`1px solid ${C.border}`,color:C.text,
              fontFamily:"'Instrument Sans',sans-serif",fontSize:12,padding:"6px 12px",
              cursor:"pointer",transition:"border-color 0.15s,background 0.15s"}}
            onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.background=C.surf;}}
            onMouseLeave={e=>{e.target.style.borderColor=C.border;e.target.style.background=C.surf2;}}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Trend Badge ───────────────────────────────────────────────────────────────
function TrendBadge({ trend }) {
  if (!trend) return null;
  const boost = trend.boost || 0;
  const col = boost > 0 ? C.green : boost < 0 ? C.red : C.muted;
  return (
    <div style={{display:"inline-flex",alignItems:"center",gap:6,background:C.surf2,
      border:`1px solid ${C.border}`,padding:"4px 10px",fontSize:10,
      fontFamily:"'Space Mono',monospace",color:col,marginTop:6}}>
      <span>Trend Score: {trend.trend_score}%</span>
      <span style={{color:C.dim}}>·</span>
      <span>Boost: {boost > 0 ? "+" : ""}{boost}</span>
    </div>
  );
}

// ─── OCR Upload Panel ─────────────────────────────────────────────────────────
function OcrPanel({ onExtract }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch(`${API_URL}/ocr`, { method: "POST", body: fd });
      const data = await r.json();
      if (data.available === false) {
        onExtract("", data.error || "OCR not available");
      } else if (data.text) {
        onExtract(data.text, null);
      } else {
        onExtract("", data.error || "No text detected");
      }
    } catch {
      onExtract("", "Cannot reach OCR endpoint");
    }
    setLoading(false);
  };

  return (
    <div style={{marginBottom:12}}>
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
        style={{border:`2px dashed ${dragging ? C.accent : C.border}`,padding:"18px",
          textAlign:"center",cursor:"pointer",transition:"border-color 0.2s",
          background:dragging?"rgba(232,255,71,0.04)":C.bg}}>
        {loading ? (
          <div>
            <div className="spin" style={{width:24,height:24,border:`2px solid ${C.border}`,
              borderTopColor:C.accent,borderRadius:"50%",margin:"0 auto 8px"}}/>
            <div style={{fontSize:11,color:C.muted,fontFamily:"'Space Mono',monospace"}}>Extracting text...</div>
          </div>
        ) : preview ? (
          <img src={preview} alt="preview" style={{maxHeight:80,maxWidth:"100%",objectFit:"contain",marginBottom:6}}/>
        ) : (
          <div>
            <div style={{fontSize:22,marginBottom:6}}>📷</div>
            <div style={{fontSize:11,color:C.muted,fontFamily:"'Space Mono',monospace"}}>
              Drop image or click to upload
            </div>
            <div style={{fontSize:10,color:C.dim,marginTop:4}}>Supports handwritten & printed forms</div>
          </div>
        )}
        <input ref={fileRef} type="file" accept="image/*" style={{display:"none"}}
          onChange={e => handleFile(e.target.files[0])} />
      </div>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function SidebarPanels() {
  return (<>
    <Panel>
      <PTitle>System Pipeline</PTitle>
      {ARCH.map((s,i) => (
        <div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"8px 0",borderBottom:i<ARCH.length-1?`1px solid ${C.border}`:"none"}}>
          <div style={{width:28,height:28,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,flexShrink:0,fontFamily:"'Space Mono',monospace",fontWeight:700,border:`1px solid ${ac(s.t)}`,background:abg(s.t),color:ac(s.t)}}>{s.l}</div>
          <div>
            <div style={{fontFamily:"'Syne',sans-serif",fontSize:13,fontWeight:600,color:C.text}}>{s.n}</div>
            <div style={{fontSize:10,color:C.dim,marginTop:1}}>{s.d}</div>
          </div>
        </div>
      ))}
    </Panel>
    <Panel>
      <PTitle>Disallowed Words</PTitle>
      <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
        {BANNED_TAGS.map(w => (
          <span key={w} style={{fontFamily:"'Space Mono',monospace",fontSize:10,padding:"3px 9px",background:"rgba(255,107,53,0.1)",border:"1px solid rgba(255,107,53,0.28)",color:C.accent2,letterSpacing:"0.05em"}}>{w}</span>
        ))}
      </div>
    </Panel>
    <Panel>
      <PTitle>Validation Rules</PTitle>
      {RULES.map((r,i) => (
        <div key={i} style={{display:"flex",alignItems:"flex-start",gap:9,padding:"8px 0",borderBottom:i<RULES.length-1?`1px solid ${C.border}`:"none",fontSize:12,color:C.muted,lineHeight:1.5}}>
          <span style={{fontFamily:"'Space Mono',monospace",fontSize:10,color:C.accent,background:"rgba(232,255,71,0.1)",padding:"2px 7px",flexShrink:0,marginTop:1}}>{r.n}</span>
          {r.t}
        </div>
      ))}
    </Panel>
  </>);
}

function HistoryPanel({ history }) {
  return (
    <Panel>
      <PTitle>Recent Submissions</PTitle>
      {history.length === 0 ? (
        <div style={{color:C.dim,fontSize:11,textAlign:"center",padding:"10px 0",fontFamily:"'Space Mono',monospace"}}>No submissions yet</div>
      ) : history.map((h,i) => (
        <div key={i} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"8px 0",borderBottom:i<history.length-1?`1px solid ${C.border}`:"none",gap:8}}>
          <div style={{minWidth:0}}>
            <div style={{fontFamily:"'Syne',sans-serif",fontSize:13,fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{h.title}</div>
            <div style={{fontSize:10,color:C.dim,fontFamily:"'Space Mono',monospace",marginTop:2}}>{h.time}</div>
          </div>
          <span style={{fontSize:9,fontFamily:"'Space Mono',monospace",padding:"3px 8px",border:"1px solid",color:vc(h.result),borderColor:vbd(h.result),flexShrink:0}}>{h.result}</span>
        </div>
      ))}
    </Panel>
  );
}

function MobileAccordion({ history }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="sidebar-mobile" style={{marginBottom:8}}>
      <button onClick={() => setOpen(o => !o)} style={{width:"100%",background:C.surf,border:`1px solid ${C.border}`,color:C.text,fontFamily:"'Space Mono',monospace",fontSize:10,letterSpacing:"0.12em",textTransform:"uppercase",padding:"12px 16px",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"space-between",position:"relative",outline:"none",marginBottom:open?0:8}}>
        <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:`linear-gradient(90deg,${C.accent3},${C.accent},transparent)`}}/>
        <span>System Info & Rules</span>
        <span style={{display:"inline-block",transition:"transform 0.3s",transform:open?"rotate(180deg)":"none"}}>▾</span>
      </button>
      {open && <div style={{animation:"fadeUp 0.25s ease",marginBottom:8}}><SidebarPanels/></div>}
      <HistoryPanel history={history}/>
    </div>
  );
}

// ─── Bulk Upload Tab ──────────────────────────────────────────────────────────
function BulkTab() {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [filename, setFilename] = useState(null);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith(".csv")) {
      setError("Please upload a CSV file"); return;
    }
    setLoading(true); setError(null); setDownloadUrl(null); setProgress("Uploading…");
    const fd = new FormData();
    fd.append("file", file);
    try {
      setProgress("Processing titles…");
      const r = await fetch(`${API_URL}/bulk`, { method: "POST", body: fd });
      if (!r.ok) {
        const e = await r.json().catch(() => ({ detail: "Server error" }));
        throw new Error(e.detail || "Bulk processing failed");
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      setFilename(`bulk_results_${Date.now()}.csv`);
      setProgress(null);
    } catch (e) {
      setError(e.message);
      setProgress(null);
    }
    setLoading(false);
  };

  return (
    <div style={{maxWidth:640,margin:"0 auto"}}>
      <Panel>
        <PTitle>Bulk Title Verification</PTitle>
        <div style={{fontSize:12,color:C.muted,marginBottom:14,lineHeight:1.7}}>
          Upload a CSV file with one title per row. The system will verify all titles in parallel and return a downloadable results file.
          <span style={{color:C.accent}}> Max 500 titles per batch.</span>
        </div>
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
          style={{border:`2px dashed ${dragging ? C.accent : C.border}`,
            padding:"40px 20px",textAlign:"center",cursor:"pointer",
            transition:"border-color 0.2s",background:dragging?"rgba(232,255,71,0.04)":C.bg,marginBottom:14}}>
          {loading ? (
            <div>
              <div className="spin" style={{width:32,height:32,border:`2px solid ${C.border}`,
                borderTopColor:C.accent,borderRadius:"50%",margin:"0 auto 12px"}}/>
              <div style={{fontSize:12,color:C.accent,fontFamily:"'Space Mono',monospace"}}>{progress}</div>
            </div>
          ) : (
            <div>
              <div style={{fontSize:36,marginBottom:10}}>📊</div>
              <div style={{fontSize:13,color:C.text,marginBottom:6,fontFamily:"'Syne',sans-serif",fontWeight:600}}>
                Drop your CSV here or click to browse
              </div>
              <div style={{fontSize:11,color:C.dim,fontFamily:"'Space Mono',monospace"}}>
                Format: first column = title names
              </div>
            </div>
          )}
          <input ref={fileRef} type="file" accept=".csv" style={{display:"none"}}
            onChange={e => handleFile(e.target.files[0])} />
        </div>

        {error && (
          <div style={{padding:"11px 14px",background:"rgba(255,77,109,0.07)",
            border:"1px solid rgba(255,77,109,0.3)",fontSize:12,color:C.red,marginBottom:10}}>
            ⚠ {error}
          </div>
        )}

        {downloadUrl && (
          <div style={{padding:"14px",background:"rgba(74,222,128,0.07)",
            border:"1px solid rgba(74,222,128,0.3)",textAlign:"center"}}>
            <div style={{fontSize:13,color:C.green,fontFamily:"'Syne',sans-serif",fontWeight:700,marginBottom:10}}>
              ✓ Processing complete!
            </div>
            <a href={downloadUrl} download={filename}
              style={{display:"inline-block",background:C.accent,color:C.bg,
                fontFamily:"'Syne',sans-serif",fontWeight:800,fontSize:12,
                letterSpacing:"0.1em",textTransform:"uppercase",padding:"10px 20px",
                textDecoration:"none",cursor:"pointer"}}>
              ↓ Download Results CSV
            </a>
          </div>
        )}
      </Panel>

      <Panel>
        <PTitle>CSV Format Guide</PTitle>
        <div style={{background:C.bg,border:`1px solid ${C.border}`,padding:"12px 14px",
          fontFamily:"'Space Mono',monospace",fontSize:11,color:C.muted,lineHeight:1.9}}>
          <div style={{color:C.accent}}>title</div>
          <div>Hindustan Morning Times</div>
          <div>Delhi Police Chronicle</div>
          <div>Prabhat Samachar</div>
          <div>Quantum Digest</div>
        </div>
        <div style={{fontSize:11,color:C.dim,marginTop:10,lineHeight:1.6}}>
          Output columns: title, verdict, verify_prob, max_sim, issues, suggestions
        </div>
      </Panel>
    </div>
  );
}

// ─── Verify Tab ────────────────────────────────────────────────────────────────
function VerifyTab({ count, setCount, hist, setHist }) {
  const [titleInput, setTitleInput] = useState("");
  const [period, setPeriod]         = useState("");
  const [lang, setLang]             = useState("en");
  const [state, setState]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [stepIdx, setStepIdx]       = useState(-1);
  const [result, setResult]         = useState(null);
  const [graphData, setGraphData]   = useState(null);
  const [iFocus, setIFocus]         = useState(false);
  const [btnHov, setBtnHov]         = useState(false);
  const [error, setError]           = useState(null);
  const [ocrError, setOcrError]     = useState(null);
  const [showOcr, setShowOcr]       = useState(false);
  const resRef = useRef(null);
  const delay = ms => new Promise(r => setTimeout(r, ms));

  const gc = result ? (result.verifyProb >= 60 ? C.green : result.verifyProb >= 30 ? C.yellow : C.red) : C.accent;

  const SELECT_STYLE = {width:"100%",background:C.bg,border:`1px solid ${C.border}`,color:C.text,fontFamily:"'Instrument Sans',sans-serif",fontSize:13,padding:"11px 32px 11px 13px",outline:"none",cursor:"pointer",appearance:"none",boxSizing:"border-box",backgroundImage:`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2344445a' stroke-width='1.5' fill='none'/%3E%3C/svg%3E")`,backgroundRepeat:"no-repeat",backgroundPosition:"right 11px center"};
  const LABEL_STYLE  = {display:"block",fontSize:10,color:C.dim,letterSpacing:"0.1em",textTransform:"uppercase",marginBottom:7,fontFamily:"'Space Mono',monospace"};

  async function verify() {
    if (!titleInput.trim() || loading) return;
    setLoading(true); setResult(null); setStepIdx(-1); setError(null); setGraphData(null);

    const apiCall = fetch(`${API_URL}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: titleInput.trim(), periodicity: period, language: lang, state }),
    });
    const graphCall = fetch(`${API_URL}/graph`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: titleInput.trim() }),
    }).then(r => r.json()).catch(() => null);

    for (let i = 0; i < PIPELINE_STEPS.length; i++) { await delay(140 + Math.random() * 150); setStepIdx(i); }
    await delay(180);

    try {
      const resp = await apiCall;
      if (!resp.ok) { const e = await resp.json().catch(() => ({ detail: "Server error" })); throw new Error(e.detail || "Verification failed"); }
      const data = await resp.json();
      const res = {
        verdict: data.verdict, verifyProb: data.verify_prob, maxSim: data.max_sim,
        simTitles: data.sim_titles, checks: data.checks, issues: data.issues,
        suggestions: data.suggestions || [], langDetected: data.lang_detected || {},
        trend: data.trend || {}, auditId: data.audit_id,
      };
      setResult(res);

      const nc = count + 1; setCount(nc); localStorage.setItem("prgi_c", nc);
      const nh = [{ title: titleInput.trim(), result: res.verdict, time: new Date().toLocaleTimeString() }, ...hist].slice(0, 5);
      setHist(nh); localStorage.setItem("prgi_h", JSON.stringify(nh));
      setTimeout(() => resRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 120);

      const gd = await graphCall;
      if (gd?.nodes) setGraphData(gd);
    } catch (err) {
      setError(err.message || "Cannot reach the verification server.");
    } finally {
      setLoading(false); setStepIdx(-1);
    }
  }

  return (
    <>
      <MobileAccordion history={hist}/>
      <div className="main-grid" style={{paddingBottom:60}}>
        {/* LEFT */}
        <div>
          <Panel>
            <PTitle>New Title Submission</PTitle>

            <div style={{display:"flex",justifyContent:"flex-end",marginBottom:8}}>
              <button onClick={() => { setShowOcr(o => !o); setOcrError(null); }}
                style={{background:showOcr?"rgba(232,255,71,0.12)":C.surf2,
                  border:`1px solid ${showOcr?C.accent:C.border}`,color:showOcr?C.accent:C.muted,
                  fontFamily:"'Space Mono',monospace",fontSize:9,letterSpacing:"0.1em",
                  textTransform:"uppercase",padding:"5px 12px",cursor:"pointer"}}>
                📷 {showOcr ? "Hide OCR" : "Upload Image (OCR)"}
              </button>
            </div>

            {showOcr && (
              <div style={{marginBottom:12}}>
                <OcrPanel onExtract={(text, err) => {
                  if (text) setTitleInput(text);
                  setOcrError(err);
                }} />
                {ocrError && <div style={{fontSize:11,color:C.red,marginTop:6,fontFamily:"'Space Mono',monospace"}}>⚠ {ocrError}</div>}
              </div>
            )}

            <div style={{marginBottom:12}}>
              <label style={LABEL_STYLE}>Title Name</label>
              <input
                style={{width:"100%",background:C.bg,border:`1px solid ${iFocus?C.accent:C.border}`,boxShadow:iFocus?`0 0 0 3px rgba(232,255,71,0.1)`:"none",color:C.text,fontFamily:"'Instrument Sans',sans-serif",fontSize:"clamp(15px,3vw,20px)",padding:"13px 15px",outline:"none",transition:"border-color 0.2s,box-shadow 0.2s",boxSizing:"border-box"}}
                placeholder="e.g. Hindustan Morning Times"
                value={titleInput}
                onChange={e => setTitleInput(e.target.value)}
                onFocus={() => setIFocus(true)}
                onBlur={() => setIFocus(false)}
                onKeyDown={e => e.key === "Enter" && verify()}
              />
            </div>

            <div className="row2" style={{marginBottom:8}}>
              <div>
                <label style={LABEL_STYLE}>Language</label>
                <select style={SELECT_STYLE} value={lang} onChange={e => setLang(e.target.value)}>
                  {[["en","English"],["hi","Hindi"],["bn","Bengali"],["mr","Marathi"],["ta","Tamil"],["te","Telugu"],["gu","Gujarati"],["kn","Kannada"],["pa","Punjabi"],["ur","Urdu"]].map(([v,l])=><option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div>
                <label style={LABEL_STYLE}>Periodicity</label>
                <select style={SELECT_STYLE} value={period} onChange={e => setPeriod(e.target.value)}>
                  {[["","Not Specified"],["daily","Daily"],["weekly","Weekly"],["biweekly","Bi-Weekly"],["monthly","Monthly"],["quarterly","Quarterly"]].map(([v,l])=><option key={v} value={v}>{l}</option>)}
                </select>
              </div>
            </div>

            <div style={{marginBottom:4}}>
              <label style={LABEL_STYLE}>State / UT (for monopoly check)</label>
              <select style={SELECT_STYLE} value={state} onChange={e => setState(e.target.value)}>
                {INDIAN_STATES.map(s => <option key={s} value={s.toLowerCase()}>{s || "Not Specified"}</option>)}
              </select>
            </div>

            <button
              style={{width:"100%",background:C.accent,color:C.bg,border:"none",fontFamily:"'Syne',sans-serif",fontSize:14,fontWeight:800,letterSpacing:"0.12em",textTransform:"uppercase",padding:"14px",cursor:loading?"not-allowed":"pointer",clipPath:"polygon(0 0,calc(100% - 11px) 0,100% 11px,100% 100%,11px 100%,0 calc(100% - 11px))",transition:"filter 0.15s,transform 0.15s",filter:btnHov&&!loading?"brightness(1.1)":"none",transform:btnHov&&!loading?"translateY(-2px)":"none",opacity:loading?0.6:1,position:"relative",overflow:"hidden",marginTop:14}}
              onMouseEnter={() => setBtnHov(true)} onMouseLeave={() => setBtnHov(false)}
              onClick={verify} disabled={loading}>
              <div style={{position:"absolute",top:0,left:"-110%",width:"60%",height:"100%",background:"linear-gradient(90deg,transparent,rgba(255,255,255,0.25),transparent)",animation:"shine 2.5s ease-in-out infinite"}}/>
              ◈ &nbsp;{loading ? "Verifying…" : "Verify Title"}
            </button>

            {error && !loading && (
              <div style={{marginTop:14,padding:"11px 14px",background:"rgba(255,77,109,0.07)",border:"1px solid rgba(255,77,109,0.3)",fontSize:12,color:C.red,lineHeight:1.7}}>
                <span style={{fontWeight:700,fontFamily:"'Space Mono',monospace",display:"block",marginBottom:2}}>⚠ CONNECTION ERROR</span>
                {error}
                <div style={{marginTop:6,fontSize:10,color:C.muted}}>Start backend: <span style={{color:C.accent,fontFamily:"'Space Mono',monospace"}}>uvicorn main:app --reload --port 8000</span></div>
              </div>
            )}

            {loading && (
              <div style={{marginTop:26,textAlign:"center",animation:"fadeUp 0.3s ease"}}>
                <div className="spin" style={{width:34,height:34,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",margin:"0 auto 12px"}}/>
                <div style={{fontFamily:"'Space Mono',monospace",fontSize:11,color:C.dim}}>Running 15-feature pipeline…</div>
                <div style={{marginTop:12,textAlign:"left",maxWidth:290,margin:"12px auto 0"}}>
                  {PIPELINE_STEPS.map((s,i) => <LoadStep key={i} text={s} status={i<stepIdx?"done":i===stepIdx?"active":"idle"}/>)}
                </div>
              </div>
            )}

            {result && !loading && (
              <div ref={resRef} style={{marginTop:22,animation:"fadeUp 0.4s ease"}}>
                {/* Verdict */}
                <div style={{padding:"15px 18px",display:"flex",alignItems:"center",gap:13,marginBottom:12,border:`1px solid ${vbd(result.verdict)}`,background:vbg(result.verdict)}}>
                  <div style={{fontSize:26,flexShrink:0}}>{result.verdict==="REJECTED"?"✗":result.verdict==="APPROVED"?"✓":"⚠"}</div>
                  <div>
                    <div className="vtitle" style={{fontFamily:"'Syne',sans-serif",fontSize:20,fontWeight:800,color:vc(result.verdict)}}>{result.verdict==="APPROVED"?"LIKELY APPROVED":result.verdict==="REVIEW"?"UNDER REVIEW":"REJECTED"}</div>
                    <div style={{fontSize:12,color:C.muted,marginTop:2}}>"{titleInput}" {result.verdict==="APPROVED"?"appears eligible":result.verdict==="REVIEW"?"requires manual review":"cannot be registered"}</div>
                  </div>
                </div>

                {/* Lang + Trend badges */}
                <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:12}}>
                  <LangBadge langDetected={result.langDetected}/>
                  <TrendBadge trend={result.trend}/>
                  {result.auditId && (
                    <div style={{display:"inline-flex",alignItems:"center",gap:6,background:C.surf2,
                      border:`1px solid ${C.border}`,padding:"4px 10px",fontSize:10,
                      fontFamily:"'Space Mono',monospace",color:C.dim}}>
                      ID: {result.auditId.slice(0,8)}
                    </div>
                  )}
                </div>

                {/* Issues */}
                {result.issues.map((iss,i) => (
                  <div key={i} style={{background:result.verdict==="REJECTED"?"rgba(255,77,109,0.06)":"rgba(251,191,36,0.06)",border:`1px solid ${result.verdict==="REJECTED"?"rgba(255,77,109,0.22)":"rgba(251,191,36,0.22)"}`,padding:"10px 13px",fontSize:12,color:C.muted,lineHeight:1.6,marginBottom:9}}>
                    <span style={{color:result.verdict==="REJECTED"?C.red:C.yellow,fontWeight:700}}>⚠ {iss.type.replace(/_/g," ").toUpperCase()}: </span>{iss.detail}
                  </div>
                ))}

                {/* Probability bar */}
                <div style={{marginBottom:16}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:7}}>
                    <span style={{fontFamily:"'Space Mono',monospace",fontSize:10,color:C.dim,textTransform:"uppercase",letterSpacing:"0.1em"}}>Verification Probability</span>
                    <span className="gpct" style={{fontFamily:"'Syne',sans-serif",fontSize:24,fontWeight:800,color:gc}}>{result.verifyProb}%</span>
                  </div>
                  <div style={{height:8,background:C.surf2,border:`1px solid ${C.border}`,overflow:"hidden"}}>
                    <div style={{height:"100%",width:`${result.verifyProb}%`,background:gc,transition:"width 1.2s cubic-bezier(0.4,0,0.2,1)"}}/>
                  </div>
                </div>

                {/* Checks */}
                <PTitle>Check Results</PTitle>
                <div className="checks-grid" style={{marginBottom:16}}>{result.checks.map((c,i) => <CheckCard key={i} {...c}/>)}</div>

                {/* Similarity Graph */}
                {graphData && <SimilarityGraph nodes={graphData.nodes} edges={graphData.edges}/>}

                {/* Similar titles */}
                <PTitle>Similar Titles Found</PTitle>
                {result.simTitles.length === 0
                  ? <div style={{color:C.dim,fontSize:11,fontFamily:"'Space Mono',monospace",padding:"6px 0"}}>No highly similar titles detected</div>
                  : result.simTitles.map((t,i) => <SimCard key={i} {...t}/>)
                }

                {/* Suggestions */}
                <SuggestionsPanel
                  suggestions={result.suggestions}
                  onPick={s => { setTitleInput(s); setResult(null); setGraphData(null); window.scrollTo({top:0,behavior:"smooth"}); }}
                />
              </div>
            )}
          </Panel>
        </div>

        {/* RIGHT desktop sidebar */}
        <div className="sidebar-desktop">
          <SidebarPanels/>
          <HistoryPanel history={hist}/>
        </div>
      </div>
    </>
  );
}

// ─── User Page (Verify + Bulk tabs) ───────────────────────────────────────────
export default function UserPage({ activeTab, count, setCount, hist, setHist }) {
  return (
    <>
      {activeTab === 0 && (
        <VerifyTab count={count} setCount={setCount} hist={hist} setHist={setHist}/>
      )}
      {activeTab === 1 && (
        <div style={{paddingBottom:60}}>
          <BulkTab/>
        </div>
      )}
    </>
  );
}
