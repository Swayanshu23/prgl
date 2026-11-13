import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { C, TABS } from "./constants";
import AdminPage from "./pages/AdminPage";
import UserPage from "./pages/UserPage";

// ─── Fonts + Keyframes ────────────────────────────────────────────────────────
const _fl = document.createElement("link");
_fl.href = "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&family=Instrument+Sans:ital,wght@0,400;0,500;1,400&display=swap";
_fl.rel = "stylesheet";
document.head.appendChild(_fl);

const _st = document.createElement("style");
_st.textContent = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  @keyframes spin    { to { transform: rotate(360deg); } }
  @keyframes blink   { 0%,100%{opacity:1}50%{opacity:0.15} }
  @keyframes fadeUp  { from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)} }
  @keyframes shine   { 0%{left:-110%}60%,100%{left:160%} }
  @keyframes pOrb    { 0%,100%{transform:scale(1)}50%{transform:scale(1.12)} }
  @keyframes pulse   { 0%,100%{opacity:0.6}50%{opacity:1} }
  .blink  { animation: blink 2s ease-in-out infinite; }
  .spin   { animation: spin 0.85s linear infinite; }
  .pulse  { animation: pulse 2s ease-in-out infinite; }
  select option { background: #0c0c18; }
  input::placeholder, textarea::placeholder { color: #f0f0f8; }
  ::-webkit-scrollbar{width:4px}
  ::-webkit-scrollbar-track{background:#0c0c18}
  ::-webkit-scrollbar-thumb{background:#2a2a3e;border-radius:2px}
  .main-grid   { display:grid; grid-template-columns:1fr clamp(260px,26%,380px); gap:20px; }
  .checks-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  .row2        { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .row3        { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }
  .sidebar-desktop { display:block; }
  .sidebar-mobile  { display:none; }
  .h1size { font-size: clamp(28px,5.5vw,66px); }
  .stat-num { font-size:clamp(12px,1.6vw,17px); }
  @media (max-width:1100px) { .main-grid { grid-template-columns:1fr 280px; } }
  @media (max-width:900px) {
    .main-grid { grid-template-columns:1fr; }
    .sidebar-desktop { display:none; } .sidebar-mobile { display:block; }
    .h1size { font-size:clamp(28px,6vw,52px); }
  }
  @media (max-width:640px) {
    .checks-grid { grid-template-columns:1fr; } .row2 { grid-template-columns:1fr; }
    .row3 { grid-template-columns:1fr 1fr; }
    .h1size { font-size:clamp(26px,7.5vw,42px); } .stat-num { font-size:12px; }
    .hflex { flex-direction:column; align-items:flex-start !important; gap:8px !important; }
    .ppd  { padding:14px 12px !important; } .hpad { padding:22px 0 16px !important; }
    .vtitle { font-size:16px !important; } .gpct { font-size:20px !important; }
    .stats-row { flex-wrap:wrap; gap:12px !important; }
  }
  @media (max-width:480px) { .h1size { font-size:clamp(22px,7.5vw,36px); } .stat-num { font-size:11px; } }
  @media (max-width:380px) { .stats-row { gap:8px !important; } .stat-num { font-size:10px; } }
`;
document.head.appendChild(_st);

// ─── App Shell ────────────────────────────────────────────────────────────────
export default function TitleVerifier() {
  const location  = useLocation();
  const navigate  = useNavigate();
  const [count, setCount] = useState(() => parseInt(localStorage.getItem("prgi_c") || "0"));
  const [hist, setHist]   = useState(() => { try { return JSON.parse(localStorage.getItem("prgi_h") || "[]"); } catch { return []; } });

  const PATH_TAB = { "/": 0, "/bulk": 1, "/admin": 2 };
  const TAB_PATH = ["/", "/bulk", "/admin"];
  const activeTab = PATH_TAB[location.pathname] ?? 0;
  const isAdmin   = activeTab === 2;

  return (
    <div style={{background:C.bg,color:C.text,minHeight:"100vh",fontFamily:"'Instrument Sans',sans-serif",position:"relative",overflowX:"hidden"}}>
      {/* BG */}
      <div style={{position:"fixed",inset:0,backgroundImage:`linear-gradient(rgba(124,92,191,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(124,92,191,0.04) 1px,transparent 1px)`,backgroundSize:"40px 40px",pointerEvents:"none",zIndex:0}}/>
      <div style={{position:"fixed",width:600,height:600,borderRadius:"50%",background:"radial-gradient(circle,rgba(124,92,191,0.15) 0%,transparent 70%)",top:-200,right:-150,pointerEvents:"none",zIndex:0,animation:"pOrb 9s ease-in-out infinite"}}/>
      <div style={{position:"fixed",width:400,height:400,borderRadius:"50%",background:"radial-gradient(circle,rgba(232,255,71,0.06) 0%,transparent 70%)",bottom:40,left:-100,pointerEvents:"none",zIndex:0,animation:"pOrb 12s ease-in-out infinite reverse"}}/>

      {/* HEADER */}
      <div style={{borderBottom:`1px solid ${C.border}`,position:"relative",zIndex:2}}>
        <div style={{padding:"14px clamp(20px,4%,64px)"}}>
          <div className="hflex" style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:12,flexWrap:"wrap"}}>
            <div style={{display:"flex",alignItems:"center",gap:12,flexShrink:0}}>
              <div style={{background:C.accent,color:C.bg,fontFamily:"'Syne',sans-serif",fontWeight:800,fontSize:12,letterSpacing:"0.1em",padding:"5px 12px",clipPath:"polygon(0 0,calc(100% - 7px) 0,100% 7px,100% 100%,7px 100%,0 calc(100% - 7px))"}}>PRGI</div>
              <div style={{fontFamily:"'Syne',sans-serif",fontSize:13,fontWeight:600,color:C.muted,lineHeight:1.35}}>
                <span style={{color:C.text}}>Title Verification</span><br/>
                <span style={{fontSize:10,color:C.dim}}>Title Compliance Engine v2.0</span>
              </div>
            </div>
            <div className="stats-row" style={{display:"flex",gap:18,flexWrap:"wrap",justifyContent:"flex-end"}}>
              {[{n:"1,60,000",l:"Titles in DB"},{n:count.toLocaleString("en-IN"),l:"Checks Today"},{n:"15",l:"Verification Features"}].map(s=>(
                <div key={s.l} style={{textAlign:"right"}}>
                  <div className="stat-num" style={{fontFamily:"'Space Mono',monospace",color:C.accent,fontWeight:700}}>{s.n}</div>
                  <div style={{fontSize:9,color:C.dim,textTransform:"uppercase",letterSpacing:"0.08em",marginTop:1}}>{s.l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Tabs */}
        <div style={{display:"flex",borderTop:`1px solid ${C.border}`,padding:"0 clamp(20px,4%,64px)"}}>
          {TABS.map((tab,i) => (
            <button key={i} onClick={() => navigate(TAB_PATH[i])}
              style={{background:"none",border:"none",borderBottom:`2px solid ${activeTab===i?C.accent:"transparent"}`,
                color:activeTab===i?C.accent:C.dim,fontFamily:"'Space Mono',monospace",fontSize:10,
                letterSpacing:"0.12em",textTransform:"uppercase",padding:"10px 18px",cursor:"pointer",
                transition:"color 0.2s,border-color 0.2s",outline:"none"}}>
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* CONTENT */}
      <div style={{padding:"0 clamp(20px,4%,64px)",position:"relative",zIndex:1}}>

        {/* HERO */}
        <div className="hpad" style={{padding:"clamp(24px,5vw,44px) 0 clamp(18px,3vw,30px)",textAlign:"center"}}>
          <div style={{display:"inline-flex",alignItems:"center",gap:8,background:C.surf,border:`1px solid ${C.border}`,padding:"5px 16px",fontSize:10,color:C.dim,letterSpacing:"0.12em",textTransform:"uppercase",fontFamily:"'Space Mono',monospace",marginBottom:18}}>
            <span className="blink" style={{width:6,height:6,borderRadius:"50%",background:C.accent,flexShrink:0,display:"inline-block"}}/>
            Innovation Hackathon 2025 · {activeTab===0?"15-Feature Pipeline":activeTab===1?"Bulk Processing":"Admin Dashboard"}
          </div>
          <h1 className="h1size" style={{fontFamily:"'Syne',sans-serif",fontWeight:800,lineHeight:1.0,letterSpacing:"-0.025em",marginBottom:13}}>
            {activeTab===0?<>Verify Before<br/><span style={{color:C.accent}}>You Publish</span></>:activeTab===1?<>Batch<br/><span style={{color:C.accent}}>Verification</span></>:<>Admin<br/><span style={{color:C.accent}}>Dashboard</span></>}
          </h1>
          <p style={{fontSize:14,color:C.muted,maxWidth:430,margin:"0 auto",lineHeight:1.65}}>
            {activeTab===0?"Semantic, phonetic & cross-language title uniqueness validation for Press Registrar General of India":activeTab===1?"Upload CSV of titles for parallel batch processing with downloadable results report":"Live monitoring, audit trail and system analytics for PRGI officers"}
          </p>
        </div>

        {/* PAGE CONTENT */}
        {isAdmin ? (
          <AdminPage/>
        ) : (
          <UserPage activeTab={activeTab} count={count} setCount={setCount} hist={hist} setHist={setHist}/>
        )}
      </div>
    </div>
  );
}
