#!/usr/bin/env python3
"""
PATENT ORACLE — Fixed for llama3 (4.7GB)
pip install requests rich python-dotenv
"""
import os, sys, json, time, base64, datetime, textwrap, argparse
from pathlib import Path

MISSING = []
try:    import requests
except: MISSING.append("requests")
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.rule import Rule
    from rich import box
except: MISSING.append("rich")
try:    from dotenv import load_dotenv
except: MISSING.append("python-dotenv")

if MISSING:
    print(f"pip install {' '.join(MISSING)}"); sys.exit(1)

for p in [Path("/home/kali/.env"), Path.home()/".env", Path(".env")]:
    if p.exists(): load_dotenv(p); break

console = Console()
EPO_AUTH   = "https://ops.epo.org/3.2/rest-services/auth/accesstoken"
EPO_SEARCH = "https://ops.epo.org/3.2/rest-services/published-data/search"

DOMAINS = [
    "Quantum Biology","Neuromorphic Materials","Synthetic Cognition",
    "Topological Chemistry","Acoustic Metamaterials","Photonic Computing",
    "DNA Data Storage","Piezoelectric Textiles","Plasma Agriculture",
    "Cryogenic Robotics","Fungal Network Computing","Gravitational Energy Harvesting",
    "Biophotonic Sensors","Quantum Entanglement Communication","Metamorphic Architecture",
    "Electrochemical Cognition","Vibrational Medicine","Symbiotic AI Hardware",
    "Tectonic Energy Capture","Exoplanet-Inspired Materials",
]

SYSTEM = """You generate novel patent ideas. Reply ONLY with JSON, no other text.
Format:
{"ideas":[{"title":"...","cross_domains":["f1","f2","f3"],"keywords":["k1","k2","k3"],"ipc_class":"X00X","mechanism":"2 sentences how it works","novelty_claim":"1 sentence what is new","human_impact":"1 sentence benefit","novelty_score":90}]}"""

def ask_ollama(base_url, model, domain, n):
    prompt = f"Generate {n} unprecedented patent invention ideas in: {domain}. Each must combine 3 different scientific fields. Reply only with JSON."
    payload = {
        "model": model, "stream": False,
        "options": {"temperature":0.9,"num_predict":800,"num_ctx":2048,"top_p":0.9},
        "messages": [
            {"role":"system","content":SYSTEM},
            {"role":"user",  "content":prompt},
        ],
    }
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    raw = r.json()["message"]["content"].strip()
    raw = raw.replace("```json","").replace("```","").strip()
    s=raw.find("{"); e=raw.rfind("}")+1
    if s==-1: raise ValueError(f"No JSON found: {raw[:200]}")
    return json.loads(raw[s:e]).get("ideas",[])

class EPOClient:
    def __init__(self,key,secret):
        self.key=key;self.secret=secret;self.token=None;self.expiry=0
    def authenticate(self):
        creds=base64.b64encode(f"{self.key}:{self.secret}".encode()).decode()
        r=requests.post(EPO_AUTH,data="grant_type=client_credentials",
            headers={"Authorization":f"Basic {creds}",
                     "Content-Type":"application/x-www-form-urlencoded"},timeout=15)
        r.raise_for_status()
        d=r.json();self.token=d["access_token"]
        self.expiry=time.time()+int(d.get("expires_in",1200))-60
    def search(self,keywords):
        if not self.token or time.time()>self.expiry: self.authenticate()
        q=" AND ".join(f'"{k}"' for k in keywords[:3])
        try:
            r=requests.get(EPO_SEARCH,
                headers={"Authorization":f"Bearer {self.token}",
                         "Accept":"application/json","X-OPS-Range":"1-3"},
                params={"q":q},timeout=20)
            if r.status_code==404: return {"found":0}
            r.raise_for_status()
            total=int(r.json().get("ops:world-patent-data",{})
                      .get("ops:biblio-search",{}).get("@total-result-count",0))
            return {"found":total,"query":q}
        except Exception as e:
            return {"found":-1,"error":str(e)}

def show_idea(idea,idx,epo=None):
    score=idea.get("novelty_score",0)
    bar="[green]"+"█"*int(score/5)+"[/][dim]"+"░"*(20-int(score/5))+f"[/] {score}/100"
    epo_s=""
    if epo:
        f=epo.get("found",-1)
        epo_s=("\n[bold green]✓ EPO: NO PRIOR ART[/]" if f==0
               else f"\n[bold yellow]⚠ EPO: {f} patents[/]" if f>0 else "")
    console.print(Panel(
        f"[bold white]{idx}. {idea.get('title','?')}[/]\n"
        f"[dim]IPC:[/] {idea.get('ipc_class','?')}  ×  "
        f"{' · '.join(idea.get('cross_domains',[]))}\n"
        f"Novelty  {bar}{epo_s}",border_style="green",padding=(1,2)))
    t=Table(show_header=False,box=box.SIMPLE,padding=(0,1))
    t.add_column("",style="dim cyan",width=16)
    t.add_column("",style="white")
    for label,key in [("Mechanism","mechanism"),("Novelty","novelty_claim"),("Impact","human_impact")]:
        v=str(idea.get(key,"—"))
        t.add_row(label,"\n".join(textwrap.wrap(v,65)))
    console.print(t);console.print()

def save(ideas,domain,epo_results,out_dir,model):
    ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base=out_dir/f"patent_{domain.replace(' ','_').lower()}_{ts}"
    base.with_suffix(".json").write_text(
        json.dumps({"domain":domain,"model":model,"ideas":
            [{**i,"epo":epo_results.get(i.get("title",""),{})} for i in ideas]
        },indent=2,ensure_ascii=False))
    lines=[f"# Patent Oracle\n**Domain:** {domain}\n\n---\n"]
    for n,idea in enumerate(ideas,1):
        epo=epo_results.get(idea.get("title",""),{})
        f=epo.get("found",-1)
        badge="✅ No prior art" if f==0 else f"⚠️ {f} patents" if f>0 else "—"
        lines.append(f"## {n}. {idea.get('title','?')}\n**EPO:** {badge} | **Novelty:** {idea.get('novelty_score',0)}/100\n\n{idea.get('mechanism','')}\n\n> {idea.get('novelty_claim','')}\n\n---\n")
    base.with_suffix(".md").write_text("\n".join(lines),encoding="utf-8")
    console.print(f"[dim]💾 {base.stem}[/]")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ollama-url","-u",default=os.getenv("OLLAMA_URL","http://localhost:11434"))
    parser.add_argument("--model","-m",default="llama3")
    parser.add_argument("--domain","-d")
    parser.add_argument("--ideas","-n",type=int,default=2)
    parser.add_argument("--no-epo",action="store_true")
    parser.add_argument("--loop",action="store_true")
    parser.add_argument("--output","-o",default="patent_reports")
    args=parser.parse_args()

    try:
        r=requests.get(f"{args.ollama_url}/api/tags",timeout=5)
        models=[m["name"] for m in r.json().get("models",[])]
        if models:
            args.model=models[0].split(":")[0]
            console.print(f"[green]✓ Ollama model:[/] [cyan]{args.model}[/]")
    except Exception as e:
        console.print(f"[red]Cannot reach Ollama: {e}[/]"); sys.exit(1)

    console.print(Panel.fit(
        f"[bold green]⚛ Patent Oracle[/]  model: [cyan]{args.model}[/]\n"
        "[dim]Optimized for llama3 4.7GB[/]",border_style="green"))

    epo_client=None
    if not args.no_epo:
        k,s=os.getenv("EPO_KEY",""),os.getenv("EPO_SECRET","")
        if k and s:
            with console.status("Authenticating EPO..."):
                try:
                    epo_client=EPOClient(k,s);epo_client.authenticate()
                    console.print("[green]✓ EPO connected[/]")
                except: console.print("[yellow]⚠ EPO failed[/]");epo_client=None
        else:
            console.print("[dim]— No EPO keys in .env[/]")

    out_dir=Path(args.output);out_dir.mkdir(parents=True,exist_ok=True)
    all_ideas=[];run=0

    while True:
        run+=1
        console.print(Rule(f"[bold green]RUN {run}[/]"))
        if args.domain and run==1: domain=args.domain
        else:
            t=Table(show_header=False,box=box.SIMPLE,padding=(0,2))
            t.add_column("#",style="dim",width=4)
            t.add_column("Domain",style="cyan")
            for i,d in enumerate(DOMAINS,1): t.add_row(str(i),d)
            console.print(t)
            c=Prompt.ask("[green]Enter number or custom domain[/]",default="1")
            domain=(DOMAINS[int(c)-1] if c.isdigit() and 1<=int(c)<=len(DOMAINS) else c)

        ideas=[]
        with Progress(SpinnerColumn(),TextColumn("[green]{task.description}"),transient=True) as p:
            task=p.add_task(f"Generating in '{domain}'...")
            try:
                ideas=ask_ollama(args.ollama_url,args.model,domain,args.ideas)
                p.update(task,description=f"✓ {len(ideas)} ideas")
            except Exception as e:
                console.print(f"[red]Error:[/] {e}")

        if not ideas:
            console.print("[red]No ideas returned.[/]")
            if not args.loop or not Confirm.ask("Retry?",default=True): break
            continue

        epo_results={}
        if epo_client:
            for idea in ideas:
                epo_results[idea.get("title","")]=epo_client.search(idea.get("keywords",[]))
                time.sleep(0.3)

        console.print(Rule("[bold green]RESULTS[/]"))
        for i,idea in enumerate(ideas,1):
            show_idea(idea,i,epo_results.get(idea.get("title","")))
        all_ideas.extend(ideas)
        save(ideas,domain,epo_results,out_dir,args.model)

        if not args.loop: break
        if not Confirm.ask("\n[green]More?[/]",default=True): break

    console.print(Panel(f"[bold green]Done![/] {len(all_ideas)} ideas.\n[dim]{out_dir.resolve()}[/]",border_style="green"))

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)
