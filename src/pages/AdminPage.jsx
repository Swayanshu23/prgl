import { useState, useCallback, useEffect } from "react";
import { C, API_URL, vc, vbd, smc } from "../constants";
import { Panel, PTitle } from "../components/SharedUI";

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [sr, hr] = await Promise.all([
        fetch(`${API_URL}/admin/stats`).then(r => r.json()),
        fetch(`${API_URL}/admin/history?limit=15`).then(r => r.json()),
      ]);
      setStats(sr);
      setHistory(hr.history || []);
    } catch {
      setError("Cannot reach admin endpoints — is the backend running?");
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect

  if (loading) return (
    <div style={{textAlign:"center",padding:"60px 20px"}}>
      <div className="spin" style={{width:34,height:34,border:`2px solid ${C.border}`,
        borderTopColor:C.accent,borderRadius:"50%",margin:"0 auto 12px"}}/>
      <div style={{fontFamily:"'Space Mono',monospace",fontSize:11,color:C.dim}}>Loading admin data…</div>
    </div>
  );

  if (error) return (
    <Panel>
      <div style={{fontSize:12,color:C.red,marginBottom:8}}>⚠ {error}</div>
      <button onClick={load} style={{background:C.surf2,border:`1px solid ${C.border}`,color:C.text,
        fontFamily:"'Space Mono',monospace",fontSize:10,padding:"7px 14px",cursor:"pointer"}}>
        ↻ Retry
      </button>
    </Panel>
  );

  const t = stats?.totals || {};
  const topIssues = stats?.top_issues || [];
  const maxIssueCount = Math.max(...topIssues.map(i => i.count), 1);
  const mongoOffline = stats?.mongo_available === false;

  return (
    <div style={{paddingBottom:60}}>
      {mongoOffline && (
        <div style={{padding:"10px 14px",background:"rgba(251,191,36,0.07)",
          border:"1px solid rgba(251,191,36,0.3)",fontSize:11,color:C.yellow,
          marginBottom:14,fontFamily:"'Space Mono',monospace"}}>
          ⚠ MongoDB offline — audit history disabled. Start mongod to enable full dashboard.
        </div>
      )}

      {/* KPI cards */}
      <div className="row3" style={{marginBottom:14}}>
        {[
          {label:"Total Verified", val:t.total||0,       col:C.accent},
          {label:"Approved",       val:t.approved||0,    col:C.green},
          {label:"Rejected",       val:t.rejected||0,    col:C.red},
          {label:"Under Review",   val:t.review||0,      col:C.yellow},
          {label:"Bulk Jobs",      val:t.bulk_jobs||0,   col:C.accent3},
          {label:"Titles in DB",   val:stats?.titles_in_db||0, col:C.muted},
        ].map((k,i) => (
          <div key={i} style={{background:C.surf,border:`1px solid ${C.border}`,
            padding:"16px 18px",position:"relative",overflow:"hidden"}}>
            <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:k.col,opacity:0.5}}/>
            <div style={{fontFamily:"'Space Mono',monospace",fontSize:20,fontWeight:700,color:k.col}}>
              {k.val.toLocaleString("en-IN")}
            </div>
            <div style={{fontSize:10,color:C.dim,textTransform:"uppercase",
              letterSpacing:"0.08em",marginTop:4}}>{k.label}</div>
          </div>
        ))}
      </div>

      <div className="row2">
        {/* Top rejection reasons */}
        <Panel>
          <PTitle>Top Rejection Reasons</PTitle>
          {topIssues.length === 0 ? (
            <div style={{color:C.dim,fontSize:11,fontFamily:"'Space Mono',monospace"}}>No rejections yet</div>
          ) : topIssues.map((iss, i) => (
            <div key={i} style={{marginBottom:10}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:4,fontSize:11}}>
                <span style={{color:C.text,fontFamily:"'Instrument Sans',sans-serif"}}>
                  {iss.type.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase())}
                </span>
                <span style={{fontFamily:"'Space Mono',monospace",color:C.accent,fontSize:10}}>{iss.count}</span>
              </div>
              <div style={{height:4,background:C.surf2,border:`1px solid ${C.border}`}}>
                <div style={{height:"100%",background:C.red,
                  width:`${(iss.count/maxIssueCount)*100}%`,transition:"width 0.8s ease"}}/>
              </div>
            </div>
          ))}
        </Panel>

        {/* Cache stats */}
        <Panel>
          <PTitle>Cache & System</PTitle>
          {stats?.cache && Object.entries(stats.cache).map(([k,v],i) => (
            <div key={i} style={{display:"flex",justifyContent:"space-between",
              padding:"7px 0",borderBottom:`1px solid ${C.border}`,fontSize:12}}>
              <span style={{color:C.muted,textTransform:"capitalize"}}>{k.replace(/_/g," ")}</span>
              <span style={{fontFamily:"'Space Mono',monospace",fontSize:11,color:C.accent}}>{String(v)}</span>
            </div>
          ))}
          <div style={{marginTop:12}}>
            <button onClick={load} style={{background:C.surf2,border:`1px solid ${C.border}`,
              color:C.text,fontFamily:"'Space Mono',monospace",fontSize:10,
              padding:"7px 14px",cursor:"pointer",letterSpacing:"0.08em"}}>
              ↻ Refresh
            </button>
          </div>
        </Panel>
      </div>

      {/* History table */}
      <Panel>
        <PTitle>Recent Verifications</PTitle>
        {history.length === 0 ? (
          <div style={{color:C.dim,fontSize:11,fontFamily:"'Space Mono',monospace"}}>No records yet</div>
        ) : (
          <div style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
              <thead>
                <tr style={{borderBottom:`1px solid ${C.border}`}}>
                  {["Title","Verdict","Prob","Max Sim","Source","Time"].map(h => (
                    <th key={h} style={{textAlign:"left",padding:"7px 10px",
                      fontFamily:"'Space Mono',monospace",fontSize:9,color:C.dim,
                      letterSpacing:"0.1em",textTransform:"uppercase"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((row, i) => (
                  <tr key={i} style={{borderBottom:`1px solid ${C.border}`,
                    background:i%2===0?C.bg:C.surf2}}>
                    <td style={{padding:"8px 10px",color:C.text,maxWidth:200,
                      overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                      {row.title}
                    </td>
                    <td style={{padding:"8px 10px"}}>
                      <span style={{fontFamily:"'Space Mono',monospace",fontSize:9,
                        padding:"3px 8px",border:"1px solid",
                        color:vc(row.verdict),borderColor:vbd(row.verdict)}}>
                        {row.verdict}
                      </span>
                    </td>
                    <td style={{padding:"8px 10px",fontFamily:"'Space Mono',monospace",color:C.muted}}>
                      {row.verify_prob}%
                    </td>
                    <td style={{padding:"8px 10px",fontFamily:"'Space Mono',monospace",color:smc(row.max_sim||0)}}>
                      {row.max_sim?.toFixed(1)}%
                    </td>
                    <td style={{padding:"8px 10px",color:C.dim,fontFamily:"'Space Mono',monospace",fontSize:9}}>
                      {row.source}
                    </td>
                    <td style={{padding:"8px 10px",color:C.dim,fontFamily:"'Space Mono',monospace",fontSize:9}}>
                      {row.created_at ? new Date(row.created_at).toLocaleTimeString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
