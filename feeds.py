import feedparser, json, os, re, time, html, urllib.request, sys
UA = "Mozilla/5.0 (compatible; CoffeeinDiscordHirek/1.0; +https://github.com/Coffeeinmod/discord-hirek)"
FEEDS = [
 ("GTA","r/GTAV_Mods","https://www.reddit.com/r/GTAV_Mods/new/.rss"),
 ("GTA","Nexus Mods GTA V","https://www.nexusmods.com/gta5/rss/newtoday"),
 ("GTA","ModDB GTA V","https://rss.moddb.com/games/grand-theft-auto-v/news/feed/rss.xml"),
 ("GTA","Rockstar Intel","https://www.rockstarintel.com/feed"),
 ("CS2","r/cs2","https://www.reddit.com/r/cs2/new/.rss"),
 ("CS2","HLTV","https://www.hltv.org/rss/news"),
 ("CS2","CounterStrikeSharp","https://github.com/roflmuffin/CounterStrikeSharp/releases.atom"),
 ("CS2","Metamod:Source","https://github.com/alliedmodders/metamod-source/releases.atom"),
 ("CS2","r/csmapmakers","https://www.reddit.com/r/csmapmakers/.rss"),
]
STATE="state.json"
state=json.load(open(STATE)) if os.path.exists(STATE) else {}
def clean(s):
    s=html.unescape(re.sub(r"<[^>]+>"," ",s or "")); s=re.sub(r"\s+"," ",s).strip()
    return s[:197]+"..." if len(s)>200 else s
def post(url,payload):
    for _ in range(3):
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","User-Agent":UA})
        try:
            urllib.request.urlopen(req,timeout=20); return True
        except urllib.error.HTTPError as e:
            if e.code==429:
                try: wait=float(json.loads(e.read()).get("retry_after",2))
                except Exception: wait=2
                time.sleep(wait+0.5); continue
            print(f"  webhook HTTP {e.code}"); return False
    return False
summary=[]
for ch,name,url in FEEDS:
    hook=os.environ.get("WEBHOOK_"+ch)
    try:
        d=feedparser.parse(url,agent=UA)
        status=getattr(d,"status",None)
        if (status and status>=400) or (d.bozo and not d.entries):
            raise Exception(f"HTTP {status} {getattr(d,'bozo_exception','')}")
        ids=[e.get("id") or e.get("link") for e in d.entries]
        first=url not in state
        seen=set(state.get(url,[]))
        new=[e for e,i in zip(d.entries,ids) if i and i not in seen]
        posted=0
        if not first and hook:
            for e in list(reversed(new[:5])):
                emb={"title":(e.get("title") or "")[:256],"url":e.get("link"),
                     "description":clean(e.get("summary")),"author":{"name":name},
                     "footer":{"text":f"Forrás: {name}"},"color":0xC8915A}
                if post(hook,{"embeds":[emb]}): posted+=1
                time.sleep(1.2)
        state[url]=list(dict.fromkeys(ids+list(seen)))[:300]
        msg=f"OK {name}: {len(d.entries)} items, {'first run (seeded)' if first else f'{len(new)} new, {posted} posted'}"
    except Exception as ex:
        msg=f"ERROR {name}: {str(ex)[:200]}"
    print(msg); summary.append(msg)
json.dump(state,open(STATE,"w"),indent=1)
