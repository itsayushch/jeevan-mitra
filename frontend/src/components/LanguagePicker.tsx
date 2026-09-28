import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, Languages } from 'lucide-react';
import type { Language } from '../types';
const languages: {code: Language; name: string; short: string}[] = [
  {code:'en', name:'English', short:'EN'}, {code:'hi', name:'हिन्दी', short:'हि'},
  {code:'ta', name:'தமிழ்', short:'த'}, {code:'bn', name:'বাংলা', short:'বা'}, {code:'te', name:'తెలుగు', short:'తె'},
];
export function LanguagePicker({language,onChange,mobile=false}: {language:Language; onChange:(value:Language)=>void; mobile?:boolean}) {
  const [open,setOpen]=useState(false);
  const root=useRef<HTMLDivElement>(null);
  const trigger=useRef<HTMLButtonElement>(null);
  useEffect(()=>{
    const close=(event:PointerEvent)=>{if (!root.current?.contains(event.target as Node)) setOpen(false);};
    document.addEventListener('pointerdown',close);
    return ()=>document.removeEventListener('pointerdown',close);
  },[]);
  const selected=languages.find(x=>x.code===language)!;
  return <div ref={root} className={`language-picker ${mobile?'mobile-language-picker':'desktop-language-picker'}`} onKeyDown={e=>{
    if(e.key==='Escape'){setOpen(false);trigger.current?.focus();}
    if(open && ['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
      e.preventDefault(); const options=Array.from(root.current!.querySelectorAll<HTMLButtonElement>('[role="menuitemradio"]'));
      const i=options.indexOf(document.activeElement as HTMLButtonElement);
      const next=e.key==='Home'?0:e.key==='End'?options.length-1:e.key==='ArrowDown'?(i+1)%options.length:(i-1+options.length)%options.length;
      options[next]?.focus();
    }
    if(e.key==='Tab') setOpen(false);
  }}>
    <button ref={trigger} className="language-trigger" aria-label={`Change language: ${selected.name}`} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}><Languages size={17}/><span>{selected.name}</span><ChevronDown size={13} className={open?'chevron-open':''}/></button>
    {open && <div className="language-menu" role="menu" aria-label="Choose language"><span className="language-menu-title">Choose language</span>{languages.map(l=><button key={l.code} role="menuitemradio" aria-checked={language===l.code} onClick={()=>{onChange(l.code);setOpen(false);trigger.current?.focus();}}><span>{l.name}</span>{language===l.code && <Check size={16}/>}</button>)}</div>}
  </div>;
}
