import { C, sc, smc, smb, smd } from "../constants";

export function PTitle({ children }) {
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
      <span style={{fontFamily:"'Space Mono',monospace",fontSize:10,fontWeight:700,letterSpacing:"0.18em",textTransform:"uppercase",color:C.dim,whiteSpace:"nowrap"}}>{children}</span>
      <div style={{flex:1,height:1,background:C.border}}/>
    </div>
  );
}

export function Panel({ children, style = {} }) {
  return (
    <div className="ppd" style={{background:C.surf,border:`1px solid ${C.border}`,padding:"22px 24px",position:"relative",overflow:"hidden",marginBottom:14,...style}}>
      <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:`linear-gradient(90deg,${C.accent3},${C.accent},transparent)`}}/>
      {children}
    </div>
  );
}

export function CheckCard({ name, status, val }) {
  const col = sc(status);
  return (
    <div style={{background:C.surf2,border:`1px solid ${C.border}`,borderLeft:`2px solid ${col}`,padding:"9px 11px",display:"flex",alignItems:"center",gap:8}}>
      <div style={{width:17,height:17,borderRadius:"50%",background:`${col}22`,color:col,display:"flex",alignItems:"center",justifyContent:"center",fontSize:9,fontWeight:700,flexShrink:0}}>
        {status==="pass"?"✓":status==="fail"?"✗":"!"}
      </div>
      <span style={{fontSize:11,color:C.muted,flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{name}</span>
      <span style={{fontFamily:"'Space Mono',monospace",fontSize:10,color:col,flexShrink:0}}>{val}</span>
    </div>
  );
}

export function SimCard({ title, score }) {
  return (
    <div style={{background:C.surf2,border:`1px solid ${C.border}`,borderLeft:`3px solid ${C.accent3}`,padding:"10px 13px",marginBottom:7,display:"flex",alignItems:"center",justifyContent:"space-between",gap:10}}>
      <div style={{minWidth:0}}>
        <div style={{fontFamily:"'Syne',sans-serif",fontSize:13,fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{title}</div>
        <div style={{fontSize:10,color:C.dim,fontFamily:"'Space Mono',monospace",marginTop:2}}>Registered · Existing DB title</div>
      </div>
      <div style={{fontFamily:"'Space Mono',monospace",fontSize:12,fontWeight:700,padding:"3px 9px",border:`1px solid ${smd(score)}`,background:smb(score),color:smc(score),flexShrink:0}}>
        {score}%
      </div>
    </div>
  );
}

export function LoadStep({ text, status }) {
  const col = status==="done"?C.green:status==="active"?C.accent:C.dim;
  return (
    <div style={{display:"flex",gap:8,padding:"3px 0",fontSize:11,color:col,fontFamily:"'Space Mono',monospace",transition:"color 0.3s"}}>
      <span className={status==="active"?"blink":""}>{status==="done"?"✓":status==="active"?"◆":"·"}</span>
      {text}
    </div>
  );
}
