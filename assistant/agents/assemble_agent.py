"""
Agents Assemble — Showcases all Jarvis agents in a highly animated HTML page.

Triggered by: "agents assemble"
    Opens a radial-layout animated HTML page. JARVIS is at the centre with
    lightning lines connecting to each agent node. A side panel shows details
    and voice intro is synced per-agent.
"""

import logging
import webbrowser
from datetime import datetime
from pathlib import Path

from assistant.agents.base_agent import BaseAgent

logger = logging.getLogger("jarvis.agents.assemble")

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

# ── Agent showcase data ────────────────────────────────────────────────────────
AGENTS_DATA = [
    {
        "name": "Portal Agent",
        "icon": "🚀",
        "color": "#6366f1",
        "description": "Your system gateway. Directly control apps, volumes, screen locks, and system environment without any trigger word.",
        "usage": "Just say: open outlook, close chrome, volume up, lock screen, take a screenshot",
        "voice_intro": "Portal Agent is your direct system controller. No trigger word needed. Just say open or close any app, control volume, lock the screen, or take a screenshot.",
    },
    {
        "name": "Morning Briefing",
        "icon": "📰",
        "color": "#f59e0b",
        "description": "Fetches your emails, calendar events, and Jira tickets, then generates a newspaper-style HTML briefing.",
        "usage": "Say: morning briefing, give briefing, newspaper",
        "voice_intro": "Morning Briefing Agent gathers your emails, calendar, and Jira tickets, then creates a beautiful newspaper page for your day.",
    },
    {
        "name": "Voice Search",
        "icon": "🔍",
        "color": "#06b6d4",
        "description": "Opens Google or YouTube search results directly. Say the platform followed by your search query.",
        "usage": "Say: search, then: YouTube latest Tamil songs, or Google Python tutorials",
        "voice_intro": "Voice Search Agent. Say search, then tell me YouTube or Google followed by what you want to find. I will open the results directly.",
    },
    {
        "name": "Web Page",
        "icon": "🌐",
        "color": "#22c55e",
        "description": "Opens configured web pages — Jira, Kanban board, CI/CD dashboard, Bitbucket repos, and more.",
        "usage": "Say: visit webpage, then: Jira, kanban board, CI/CD board, or [repo] in bitbucket",
        "voice_intro": "Web Page Agent opens your work tools. Say visit webpage, then tell me which page: Jira, kanban board, CI CD board, or any repository in Bitbucket.",
    },
    {
        "name": "Thanos",
        "icon": "🫰",
        "color": "#ef4444",
        "description": "Snaps all running applications closed. A clean slate for your desktop in one command.",
        "usage": "Say: thanos",
        "voice_intro": "Thanos Agent. One word: thanos. And all running apps get snapped away, giving you a clean desktop instantly.",
    },
]


def _generate_html() -> str:
    """Generate the Agents Assemble animated HTML page — static radial layout."""

    agents_js = ",\n            ".join(
        (
            f'{{"name": "{a["name"]}", "icon": "{a["icon"]}", "color": "{a["color"]}", '
            f'"description": "{a["description"]}", "usage": "{a["usage"]}", '
            f'"voice_intro": "{a["voice_intro"]}"}}'
        )
        for a in AGENTS_DATA
    )

    return (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "    <meta charset='UTF-8'>\n"
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "    <title>Jarvis - Agents Assemble</title>\n"
        "    <style>\n"
        "        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');\n"
        "        * { margin: 0; padding: 0; box-sizing: border-box; }\n"
        "        body {\n"
        "            background: radial-gradient(ellipse at center, #0d0d2b 0%, #050510 100%);\n"
        "            font-family: 'Exo 2', 'Segoe UI', sans-serif;\n"
        "            overflow: hidden; height: 100vh; width: 100vw;\n"
        "            display: flex; flex-direction: column;\n"
        "            align-items: center; justify-content: center;\n"
        "        }\n"
        "        .stars { position: fixed; inset: 0; z-index: 0; overflow: hidden; }\n"
        "        .star { position: absolute; border-radius: 50%; background: white; animation: twinkle linear infinite; }\n"
        "        @keyframes twinkle { 0%,100%{ opacity:0.1; } 50%{ opacity:0.9; } }\n"
        "        .title-bar {\n"
        "            position: fixed; top: 24px; left: 50%; transform: translateX(-50%);\n"
        "            text-align: center; z-index: 100; animation: fadeDown 1s ease-out both;\n"
        "        }\n"
        "        @keyframes fadeDown {\n"
        "            from{ opacity:0; transform:translateX(-50%) translateY(-20px); }\n"
        "            to  { opacity:1; transform:translateX(-50%) translateY(0); }\n"
        "        }\n"
        "        .title-bar h1 {\n"
        "            font-family:'Orbitron',monospace; font-size:2rem; font-weight:900;\n"
        "            letter-spacing:8px;\n"
        "            background:linear-gradient(90deg,#6366f1,#06b6d4,#22c55e,#f59e0b);\n"
        "            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;\n"
        "        }\n"
        "        .title-bar p { color:rgba(255,255,255,0.4); font-size:0.75rem; letter-spacing:4px; margin-top:4px; text-transform:uppercase; }\n"
        "        #canvas-wrap { position:relative; width:700px; height:700px; z-index:10; }\n"
        "        svg#connections { position:absolute; inset:0; width:100%; height:100%; overflow:visible; }\n"
        "        .center-orb {\n"
        "            position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);\n"
        "            width:120px; height:120px; border-radius:50%;\n"
        "            background:radial-gradient(circle at 35% 35%,#4f46e5,#1e1b4b);\n"
        "            display:flex; flex-direction:column; align-items:center; justify-content:center;\n"
        "            z-index:30;\n"
        "            box-shadow:0 0 0 3px rgba(99,102,241,0.6),0 0 35px rgba(99,102,241,0.5),0 0 90px rgba(99,102,241,0.2);\n"
        "            animation:orbBreath 3s ease-in-out infinite;\n"
        "        }\n"
        "        @keyframes orbBreath {\n"
        "            0%,100%{ box-shadow:0 0 0 3px rgba(99,102,241,0.6),0 0 35px rgba(99,102,241,0.5),0 0 90px rgba(99,102,241,0.2); }\n"
        "            50%    { box-shadow:0 0 0 5px rgba(99,102,241,0.9),0 0 55px rgba(99,102,241,0.8),0 0 130px rgba(99,102,241,0.4); }\n"
        "        }\n"
        "        .orb-label { font-family:'Orbitron',monospace; font-size:1rem; font-weight:900; color:#a5b4fc; letter-spacing:3px; }\n"
        "        .orb-sub   { font-size:0.55rem; color:rgba(165,180,252,0.6); letter-spacing:2px; margin-top:3px; text-transform:uppercase; }\n"
        "        .agent-node {\n"
        "            position:absolute; width:120px; height:120px;\n"
        "            transform:translate(-50%,-50%);\n"
        "            cursor:pointer; z-index:20;\n"
        "            animation:nodeFadeIn 0.6s ease-out both;\n"
        "        }\n"
        "        @keyframes nodeFadeIn {\n"
        "            from{ opacity:0; transform:translate(-50%,-50%) scale(0.2); }\n"
        "            to  { opacity:1; transform:translate(-50%,-50%) scale(1); }\n"
        "        }\n"
        "        .node-inner {\n"
        "            width:100%; height:100%; border-radius:50%;\n"
        "            background:rgba(10,10,30,0.92);\n"
        "            display:flex; flex-direction:column; align-items:center; justify-content:center;\n"
        "            border:2px solid var(--color);\n"
        "            box-shadow:0 0 18px var(--color),inset 0 0 18px rgba(0,0,0,0.5);\n"
        "            transition:all 0.35s ease; position:relative; overflow:hidden;\n"
        "        }\n"
        "        .node-inner::before {\n"
        "            content:''; position:absolute; inset:-6px; border-radius:50%;\n"
        "            border:2px solid transparent;\n"
        "            border-top-color:var(--color); border-right-color:var(--color);\n"
        "            animation:ringRotate 4s linear infinite;\n"
        "        }\n"
        "        @keyframes ringRotate { to{ transform:rotate(360deg); } }\n"
        "        .agent-node.active .node-inner,\n"
        "        .agent-node:hover  .node-inner {\n"
        "            background:rgba(20,20,55,0.98);\n"
        "            box-shadow:0 0 55px var(--color),0 0 110px rgba(0,0,0,0.3),inset 0 0 22px rgba(255,255,255,0.05);\n"
        "            transform:scale(1.18);\n"
        "        }\n"
        "        .agent-node.active .node-inner::before,\n"
        "        .agent-node:hover  .node-inner::before { animation-duration:0.8s; border-color:var(--color); }\n"
        "        .node-icon { font-size:2.4rem; line-height:1; filter:drop-shadow(0 0 8px var(--color)); }\n"
        "        .node-name {\n"
        "            font-family:'Orbitron',monospace; font-size:0.52rem; font-weight:700;\n"
        "            color:white; text-align:center; margin-top:5px;\n"
        "            letter-spacing:1px; text-transform:uppercase; padding:0 6px; line-height:1.3;\n"
        "        }\n"
        "        #info-panel {\n"
        "            position:fixed; right:0; top:50%;\n"
        "            transform:translateY(-50%) translateX(110%);\n"
        "            width:300px;\n"
        "            background:rgba(8,8,28,0.97);\n"
        "            backdrop-filter:blur(22px);\n"
        "            border-left:1px solid rgba(99,102,241,0.35);\n"
        "            border-top:1px solid rgba(99,102,241,0.2);\n"
        "            border-bottom:1px solid rgba(99,102,241,0.2);\n"
        "            border-radius:20px 0 0 20px;\n"
        "            padding:28px 22px; z-index:200;\n"
        "            transition:transform 0.5s cubic-bezier(0.34,1.56,0.64,1);\n"
        "        }\n"
        "        #info-panel.visible { transform:translateY(-50%) translateX(0); }\n"
        "        #info-icon {\n"
        "            font-size:3rem; display:block; text-align:center;\n"
        "            filter:drop-shadow(0 0 14px var(--panel-color,#6366f1)); margin-bottom:10px;\n"
        "        }\n"
        "        #info-name {\n"
        "            font-family:'Orbitron',monospace; font-size:0.95rem; font-weight:700;\n"
        "            text-align:center; color:white; margin-bottom:12px; letter-spacing:2px;\n"
        "        }\n"
        "        .info-divider {\n"
        "            height:1px;\n"
        "            background:linear-gradient(90deg,transparent,var(--panel-color,#6366f1),transparent);\n"
        "            margin-bottom:14px;\n"
        "        }\n"
        "        #info-desc { color:rgba(255,255,255,0.78); font-size:0.82rem; line-height:1.65; margin-bottom:14px; }\n"
        "        #info-usage {\n"
        "            background:rgba(99,102,241,0.08);\n"
        "            border:1px solid rgba(99,102,241,0.25);\n"
        "            border-radius:10px; padding:10px 12px;\n"
        "            font-size:0.78rem; color:#a5b4fc;\n"
        "            font-family:'Cascadia Code','Fira Code',monospace; line-height:1.5;\n"
        "        }\n"
        "        .usage-label { font-size:0.6rem; letter-spacing:2px; color:rgba(165,180,252,0.5); text-transform:uppercase; margin-bottom:4px; }\n"
        "        #progress-dots {\n"
        "            position:fixed; bottom:28px; left:50%; transform:translateX(-50%);\n"
        "            display:flex; gap:10px; z-index:100;\n"
        "        }\n"
        "        .dot {\n"
        "            width:10px; height:10px; border-radius:50%;\n"
        "            background:rgba(255,255,255,0.2); border:1px solid rgba(255,255,255,0.3);\n"
        "            cursor:pointer; transition:all 0.3s ease;\n"
        "        }\n"
        "        .dot.active {\n"
        "            background:var(--dot-color,#6366f1);\n"
        "            box-shadow:0 0 10px var(--dot-color,#6366f1);\n"
        "            transform:scale(1.35);\n"
        "        }\n"
        "        .thunder-path {\n"
        "            stroke-linecap:round; stroke-linejoin:round; fill:none;\n"
        "            stroke-dasharray:300; stroke-dashoffset:300;\n"
        "            animation:dashIn 1.2s ease-out forwards, pulseLine 2.5s ease-in-out infinite 1.2s;\n"
        "        }\n"
        "        @keyframes dashIn { to{ stroke-dashoffset:0; } }\n"
        "        @keyframes pulseLine { 0%,100%{ opacity:0.3; } 50%{ opacity:0.85; } }\n"
        "        .thunder-bolt { font-size:1rem; text-align:center; animation:boltFlash 2s ease-in-out infinite; }\n"
        "        @keyframes boltFlash { 0%,100%{ opacity:0.5; } 50%{ opacity:1; filter:drop-shadow(0 0 6px #facc15); } }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <div class='stars' id='stars'></div>\n"
        "    <div class='title-bar'>\n"
        "        <h1>AGENTS ASSEMBLE</h1>\n"
        "        <p>Jarvis Agent Ecosystem &bull; Click an agent to explore</p>\n"
        "    </div>\n"
        "    <div id='canvas-wrap'>\n"
        "        <svg id='connections'></svg>\n"
        "        <div class='center-orb'>\n"
        "            <span class='orb-label'>JARVIS</span>\n"
        "            <span class='orb-sub'>Core AI</span>\n"
        "        </div>\n"
        "    </div>\n"
        "    <div id='info-panel'>\n"
        "        <span id='info-icon'>&#x26A1;</span>\n"
        "        <div id='info-name'>SELECT AN AGENT</div>\n"
        "        <div class='info-divider'></div>\n"
        "        <p id='info-desc'>Click or hover any agent node to learn what it does. Auto-showcase will begin shortly.</p>\n"
        "        <div id='info-usage'></div>\n"
        "    </div>\n"
        "    <div id='progress-dots'></div>\n"
        "    <script>\n"
        f"        const agents = [{agents_js}];\n"
        "        const CX=350, CY=350, RADIUS=230, AUTO_MS=6000;\n"
        "        const starsEl=document.getElementById('stars');\n"
        "        for(let i=0;i<130;i++){\n"
        "            const s=document.createElement('div'); s.className='star';\n"
        "            const sz=Math.random()*2.5+0.5;\n"
        "            s.style.cssText=`width:${sz}px;height:${sz}px;left:${Math.random()*100}vw;top:${Math.random()*100}vh;animation-duration:${2+Math.random()*5}s;animation-delay:${Math.random()*5}s;`;\n"
        "            starsEl.appendChild(s);\n"
        "        }\n"
        "        const svg=document.getElementById('connections');\n"
        "        const wrap=document.getElementById('canvas-wrap');\n"
        "        const panel=document.getElementById('info-panel');\n"
        "        const dots=document.getElementById('progress-dots');\n"
        "        const nodeEls=[];\n"
        "        agents.forEach((ag,i)=>{\n"
        "            const angle=(2*Math.PI*i/agents.length)-Math.PI/2;\n"
        "            const x=CX+RADIUS*Math.cos(angle), y=CY+RADIUS*Math.sin(angle);\n"
        "            const mx=(CX+x)/2, my=(CY+y)/2;\n"
        "            const dx=x-CX, dy=y-CY;\n"
        "            const perp={x:-dy*0.10, y:dx*0.10};\n"
        "            const path=document.createElementNS('http://www.w3.org/2000/svg','path');\n"
        "            path.setAttribute('d',`M${CX},${CY} L${mx+perp.x},${my+perp.y} L${x},${y}`);\n"
        "            path.setAttribute('class','thunder-path');\n"
        "            path.setAttribute('stroke',ag.color);\n"
        "            path.setAttribute('stroke-width','2');\n"
        "            path.style.animationDelay=`${i*0.18}s, ${i*0.18+1.2}s`;\n"
        "            svg.appendChild(path);\n"
        "            const fo=document.createElementNS('http://www.w3.org/2000/svg','foreignObject');\n"
        "            fo.setAttribute('x',mx+perp.x-11); fo.setAttribute('y',my+perp.y-13);\n"
        "            fo.setAttribute('width','22'); fo.setAttribute('height','22');\n"
        "            fo.innerHTML=`<div xmlns='http://www.w3.org/1999/xhtml' class='thunder-bolt'>&#x26A1;</div>`;\n"
        "            fo.style.animationDelay=`${i*0.25}s`;\n"
        "            svg.appendChild(fo);\n"
        "            const node=document.createElement('div');\n"
        "            node.className='agent-node'; node.id=`node-${i}`;\n"
        "            node.style.cssText=`left:${x}px;top:${y}px;--color:${ag.color};animation-delay:${i*0.15+0.4}s;`;\n"
        "            node.innerHTML=`<div class='node-inner'><span class='node-icon'>${ag.icon}</span><span class='node-name'>${ag.name}</span></div>`;\n"
        "            node.addEventListener('mouseenter',()=>{clearAuto();showAgent(i);});\n"
        "            node.addEventListener('click',()=>{clearAuto();showAgent(i);});\n"
        "            wrap.appendChild(node); nodeEls.push(node);\n"
        "            const dot=document.createElement('div'); dot.className='dot';\n"
        "            dot.style.setProperty('--dot-color',ag.color);\n"
        "            dot.addEventListener('click',()=>{clearAuto();showAgent(i);});\n"
        "            dots.appendChild(dot);\n"
        "        });\n"
        "        let currentIdx=-1;\n"
        "        function showAgent(i){\n"
        "            currentIdx=i; const ag=agents[i];\n"
        "            nodeEls.forEach((n,idx)=>n.classList.toggle('active',idx===i));\n"
        "            dots.querySelectorAll('.dot').forEach((d,idx)=>d.classList.toggle('active',idx===i));\n"
        "            panel.style.setProperty('--panel-color',ag.color);\n"
        "            document.getElementById('info-icon').textContent=ag.icon;\n"
        "            document.getElementById('info-name').textContent=ag.name;\n"
        "            document.getElementById('info-desc').textContent=ag.description;\n"
        "            document.getElementById('info-usage').innerHTML=`<div class='usage-label'>How to use</div>${ag.usage}`;\n"
        "            panel.classList.add('visible');\n"
        "        }\n"
        "        let autoIdx=0, autoTimer=null;\n"
        "        function autoNext(){ showAgent(autoIdx%agents.length); autoIdx++; autoTimer=setTimeout(autoNext,AUTO_MS); }\n"
        "        function clearAuto(){ clearTimeout(autoTimer); autoTimer=null; }\n"
        "        setTimeout(autoNext,1800);\n"
        "    </script>\n"
        "</body>\n"
        "</html>"
    )


class AssembleAgent(BaseAgent):
    """Opens an animated HTML page showcasing all Jarvis agents."""

    name = "Agents Assemble"
    triggers = ["agents_assemble"]

    def __init__(self, settings: dict, ai_manager=None):
        super().__init__(settings, ai_manager)
        self._status_emit = None

    def run(self, data: dict | None = None) -> str:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate & save HTML
        html_content = _generate_html()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"agents_assemble_{timestamp}.html"
        filepath = OUTPUT_DIR / filename
        filepath.write_text(html_content, encoding="utf-8")

        # Open in default browser
        webbrowser.open(str(filepath))
        logger.info(f"Agents Assemble page opened: {filepath}")

        # Opening line spoken while the page loads
        opening = "Agents, assemble! Here is your Jarvis agent ecosystem."
        if self._status_emit:
            self._status_emit(opening)

        # Voice intros emitted one-per-agent; TTS queue paces them to match
        # the 6-second per-agent visual auto-showcase cycle.
        for agent in AGENTS_DATA:
            if self._status_emit:
                self._status_emit(agent["voice_intro"])

        return opening
