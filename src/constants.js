// ─── API ───────────────────────────────────────────────────────────────────────
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Pipeline / Architecture / Rules ──────────────────────────────────────────
export const PIPELINE_STEPS = [
  "Normalizing & transliteration-normalizing",
  "Language auto-detection",
  "Disallowed words + offensive content",
  "Trademark & acronym conflict check",
  "Phonetic matching (Soundex / Metaphone)",
  "Fuzzy string similarity (160K titles)",
  "Semantic embedding comparison",
  "Cross-language translation check",
  "State monopoly & trend scoring",
  "Score aggregation → verdict",
];

export const ARCH = [
  {t:"a",l:"01",n:"Preprocessing",d:"Normalize · Transliterate · Strip affixes"},
  {t:"b",l:"02",n:"Phonetic Engine",d:"Soundex · Metaphone · NYSIIS"},
  {t:"a",l:"03",n:"Fuzzy Matching",d:"Levenshtein · Jaro-Winkler · n-gram"},
  {t:"b",l:"04",n:"Semantic Search",d:"Multilingual SBERT + FAISS index"},
  {t:"c",l:"05",n:"Compliance Rules",d:"Banned words · Periodicity · Combos"},
  {t:"a",l:"06",n:"Score Aggregation",d:"Weighted ensemble → P(verify) score"},
  {t:"b",l:"07",n:"Cross-Language",d:"Prabhat≈Morning · Surya≈Sun"},
  {t:"c",l:"08",n:"Trademark Check",d:"Brand names · Acronym expansion"},
];

export const RULES = [
  {n:"R1",t:"Phonetically similar titles rejected (Namaskar ≈ Namascar)"},
  {n:"R2",t:"Cross-language duplicates blocked (Pratidin Sandhya ≈ Daily Evening)"},
  {n:"R3",t:"Combination of existing titles not allowed"},
  {n:"R4",t:"Periodicity suffixes to existing titles blocked"},
  {n:"R5",t:"Trademark and brand name conflicts flagged"},
  {n:"R6",t:"Acronym expansion checked (HT = Hindustan Times)"},
  {n:"R7",t:"State-wise saturation prevents regional monopoly"},
];

export const BANNED_TAGS = ["POLICE","CRIME","CBI","CID","ARMY","NAVY","RAW","IB","TERROR","BOMB","DRUG","MAFIA","GANG","MURDER","SCAM"];

export const TABS = ["Verify","Bulk Upload","Admin"];

export const LANG_FLAGS = {"en":"🇬🇧","hi":"🇮🇳","bn":"🇧🇩","ta":"🇮🇳","te":"🇮🇳","gu":"🇮🇳","kn":"🇮🇳","ml":"🇮🇳","pa":"🇮🇳","ur":"🇵🇰","mr":"🇮🇳"};

export const INDIAN_STATES = [
  "","Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa",
  "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
  "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
  "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
  "Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh",
];

// ─── Colors ────────────────────────────────────────────────────────────────────
export const C = {bg:"#080810",surf:"#0e0e1a",surf2:"#141420",border:"#1e1e2e",accent:"#e8ff47",accent2:"#ff6b35",accent3:"#7c5cbf",text:"#f0f0f8",muted:"#f0f0f8",dim:"#f0f0f8",green:"#4ade80",red:"#ff4d6d",yellow:"#fbbf24"};

// ─── Color Helpers ─────────────────────────────────────────────────────────────
export const sc  = s => s==="pass"?C.green:s==="fail"?C.red:C.yellow;
export const vc  = v => v==="APPROVED"?C.green:v==="REJECTED"?C.red:C.yellow;
export const vbg = v => v==="APPROVED"?"rgba(74,222,128,0.07)":v==="REJECTED"?"rgba(255,77,109,0.07)":"rgba(251,191,36,0.07)";
export const vbd = v => v==="APPROVED"?"rgba(74,222,128,0.35)":v==="REJECTED"?"rgba(255,77,109,0.35)":"rgba(251,191,36,0.35)";
export const ac  = t => t==="a"?C.accent:t==="b"?C.accent3:C.accent2;
export const abg = t => t==="a"?"rgba(232,255,71,0.1)":t==="b"?"rgba(124,92,191,0.1)":"rgba(255,107,53,0.1)";
export const smc = s => s>=80?C.red:s>=60?C.yellow:C.green;
export const smb = s => s>=80?"rgba(255,77,109,0.1)":s>=60?"rgba(251,191,36,0.1)":"rgba(74,222,128,0.1)";
export const smd = s => s>=80?"rgba(255,77,109,0.4)":s>=60?"rgba(251,191,36,0.4)":"rgba(74,222,128,0.4)";
