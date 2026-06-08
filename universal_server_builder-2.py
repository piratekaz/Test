#!/usr/bin/env python3
"""
SERTA v3.2 — Universal Server Builder
Folder upload · Bot Hosting · Web · Storage · App
"""
import sys,os,json,time,socket,shutil,secrets,hashlib,logging
import sqlite3,platform,datetime,threading,subprocess,traceback
import re,signal,textwrap,mimetypes,zipfile,urllib.request,html as _html
from pathlib import Path
from typing import Optional,Dict,Any,List

# ── SECTION 1: COLOURS ──────────────────────────────────────────────────────
class C:
    RESET="\033[0m";BOLD="\033[1m";DIM="\033[2m";ITALIC="\033[3m"
    RED="\033[31m";GREEN="\033[32m";YELLOW="\033[33m";BLUE="\033[34m"
    MAGENTA="\033[35m";CYAN="\033[36m";WHITE="\033[37m"
    BRED="\033[91m";BGREEN="\033[92m";BYELLOW="\033[93m"
    BBLUE="\033[94m";BMAGENTA="\033[95m";BCYAN="\033[96m";BWHITE="\033[97m"
    BG_BLACK="\033[40m";BG_RED="\033[41m";BG_GREEN="\033[42m"
    BG_BLUE="\033[44m";BG_CYAN="\033[46m"
    @staticmethod
    def enable_windows():
        if sys.platform=="win32":
            try:
                import ctypes;k=ctypes.windll.kernel32;k.SetConsoleMode(k.GetStdHandle(-11),7)
            except Exception:pass
C.enable_windows()

# ── SECTION 2: PRINT HELPERS ─────────────────────────────────────────────────
try:
    TERM_WIDTH=min(shutil.get_terminal_size((90,24)).columns,100)
    if TERM_WIDTH<20:TERM_WIDTH=80  # guard against invalid terminal size
except Exception:
    TERM_WIDTH=80
def hr(ch="─",color=C.DIM):print(f"{color}{ch*TERM_WIDTH}{C.RESET}")
def banner():
    lines=["   ███████╗███████╗██████╗ ████████╗ █████╗ ",
           "   ██╔════╝██╔════╝██╔══██╗╚══██╔══╝██╔══██╗",
           "   ███████╗█████╗  ██████╔╝   ██║   ███████║",
           "   ╚════██║██╔══╝  ██╔══██╗   ██║   ██╔══██║",
           "   ███████║███████╗██║  ██║   ██║   ██║  ██║",
           "   ╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"]
    print()
    for l in lines:print(f"{C.BCYAN}{C.BOLD}{l}{C.RESET}")
    print(f"{C.BYELLOW}{C.BOLD}{'Server Creation & Automation · Universal Server Builder v3.2'.center(TERM_WIDTH)}{C.RESET}")
    print(f"{C.DIM}{'Flask · SQLite · Cloudflare Tunnels · Folder Upload · Bot Hosting'.center(TERM_WIDTH)}{C.RESET}")
    hr("═",C.CYAN)
def ok(m):print(f"  {C.BGREEN}✔{C.RESET}  {m}")
def warn(m):print(f"  {C.BYELLOW}⚠{C.RESET}  {m}")
def err(m):print(f"  {C.BRED}✖{C.RESET}  {m}")
def info(m):print(f"  {C.BBLUE}ℹ{C.RESET}  {m}")
def step(m):print(f"  {C.BMAGENTA}→{C.RESET}  {m}")
def section(t):print();hr();print(f"  {C.BOLD}{C.BWHITE}{t}{C.RESET}");hr()
def progress_bar(label,steps=20,delay=0.04):
    sys.stdout.write(f"  {C.DIM}{label}  {C.RESET}[");sys.stdout.flush()
    for i in range(steps):
        time.sleep(delay);sys.stdout.write(f"{C.BGREEN if i>=steps-1 else C.BCYAN}█{C.RESET}");sys.stdout.flush()
    print(f"] {C.BGREEN}Done{C.RESET}")
def spinner(label,duration=1.2):
    frames=["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];end=time.time()+duration;i=0
    while time.time()<end:
        sys.stdout.write(f"\r  {C.BCYAN}{frames[i%len(frames)]}{C.RESET}  {label} ");sys.stdout.flush();time.sleep(0.1);i+=1
    sys.stdout.write(f"\r  {C.BGREEN}✔{C.RESET}  {label}       \n");sys.stdout.flush()
def menu(title,options):
    print(f"\n  {C.BOLD}{C.BYELLOW}{title}{C.RESET}");hr("·",C.DIM)
    for k,l in options:print(f"    {C.BCYAN}[{k}]{C.RESET}  {l}")
    hr("·",C.DIM)
    return input(f"  {C.BWHITE}Enter choice:{C.RESET} ").strip().lower()
def confirm(p,default=False):
    hint="[Y/n]" if default else "[y/N]"
    a=input(f"  {C.BYELLOW}?{C.RESET}  {p} {C.DIM}{hint}{C.RESET} ").strip().lower()
    return default if not a else a.startswith("y")
def prompt(label,default=""):
    hint=f" {C.DIM}(default: {default}){C.RESET}" if default else ""
    v=input(f"  {C.BCYAN}▸{C.RESET}  {label}{hint}: ").strip()
    return v if v else default

# ── SECTION 3: STARTUP ───────────────────────────────────────────────────────
def check_python_version():
    section("Python Version Check")
    major,minor=sys.version_info[:2]
    if major<3 or (major==3 and minor<8):err(f"Python {major}.{minor} — need 3.8+");sys.exit(1)
    ok(f"Python {major}.{minor} ✓");ok(f"Platform: {platform.system()} {platform.release()}")
def check_network():
    section("Network Connectivity")
    for host,port in [("8.8.8.8",53),("1.1.1.1",53)]:
        try:
            s=socket.create_connection((host,port),timeout=3);s.close()
            ok(f"Internet reachable via {host}:{port}");return True
        except OSError:pass
    warn("No internet — tunnels unavailable.");return False
def install_package(pkg):
    step(f"Installing {pkg}…")
    r=subprocess.run([sys.executable,"-m","pip","install",pkg,"--quiet"],capture_output=True,text=True)
    if r.returncode==0:ok(f"{pkg} installed.")
    else:err(f"Failed: {r.stderr}");sys.exit(1)
def check_flask():
    section("Flask Dependency Check")
    try:import flask,flask_sqlalchemy;ok("Flask + Flask-SQLAlchemy ✓")
    except ImportError:
        warn("Flask not found — installing…");install_package("flask");install_package("flask-sqlalchemy")
def check_werkzeug():
    try:from werkzeug.utils import secure_filename;ok("Werkzeug ✓")
    except ImportError:install_package("werkzeug")
def run_startup_checks():
    check_python_version();network_ok=check_network();check_flask();check_werkzeug()
    progress_bar("Finalising environment",steps=15,delay=0.03);return network_ok

# ── SECTION 4: PROJECT MANAGEMENT ────────────────────────────────────────────
PROJECTS_DIR=Path.home()/".serta_projects"
def list_projects():
    PROJECTS_DIR.mkdir(parents=True,exist_ok=True)
    return sorted([p for p in PROJECTS_DIR.iterdir() if p.is_dir()])
def load_config(project_dir):
    f=project_dir/"usb_config.json"
    return json.loads(f.read_text()) if f.exists() else {}
def save_config(project_dir,config):
    (project_dir/"usb_config.json").write_text(json.dumps(config,indent=2))
def generate_readme(project_dir,config):
    port=config.get("port",5000);name=config.get("name",project_dir.name)
    stype=config.get("server_type","?").replace("_"," ").title()
    (project_dir/"README.md").write_text(textwrap.dedent(f"""\
        # {name}  —  Serta v3.2
        **Type:** {stype} | **Port:** {port}
        Start: `python universal_server_builder.py`
        Local: http://127.0.0.1:{port}
        Admin: http://127.0.0.1:{port}/admin
    """))

def _hash_password(pw, salt=None):
    """PBKDF2-HMAC-SHA256 with per-project salt. Returns 'salt$hash' string."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 260000)
    return f"{salt}${dk.hex()}"

def check_password(pw, stored):
    """Verify password against stored 'salt$hash' or legacy sha256 hash."""
    if "$" in stored:
        salt, _ = stored.split("$", 1)
        return secrets.compare_digest(_hash_password(pw, salt), stored)
    # Legacy plain sha256 fallback (projects created before this fix)
    legacy = hashlib.sha256(f"serta_v3_salt_2024{pw}".encode()).hexdigest()
    return secrets.compare_digest(legacy, stored)

def create_project():
    section("Create New Serta Project")
    name=prompt("Project name","serta").replace(" ","_")
    project_dir=PROJECTS_DIR/name
    if project_dir.exists():
        warn(f"'{name}' already exists.")
        if not confirm("Overwrite?",default=False):return None
    project_dir.mkdir(parents=True,exist_ok=True)
    stype=menu("Server Type",[
        ("1","Web Server          — folder upload, static site hosting, admin panel"),
        ("2","Application Server  — REST API + SQLite"),
        ("3","File Storage Server — folder upload, download, manage"),
        ("4","Bot Hosting         — Discord / Telegram / Slack / Generic Python bot"),
    ])
    type_map={"1":"web","2":"app","3":"storage","4":"bot"}
    server_type=type_map.get(stype,"web")
    port_str=prompt("Port","5000")
    try:port=int(port_str)
    except:port=5000
    admin_pw=prompt("Admin password","admin")
    config:Dict[str,Any]={
        "name":name,"server_type":server_type,"port":port,
        "secret_key":secrets.token_hex(32),"created":str(datetime.date.today()),
        "project_dir":str(project_dir),"admin_password_hash":_hash_password(admin_pw),
    }
    if server_type=="web":
        (project_dir/"site").mkdir(exist_ok=True)
        config["hosted_entry"]=None;config["site_dir"]=str(project_dir/"site")
    elif server_type=="app":
        (project_dir/"data").mkdir(exist_ok=True)
        config["db_path"]=str(project_dir/"data"/"app.db")
    elif server_type=="storage":
        (project_dir/"files").mkdir(exist_ok=True)
        config["storage_auth"]=confirm("Enable login protection?",default=True)
    elif server_type=="bot":
        config=_configure_bot(config,project_dir)
    save_config(project_dir,config);generate_readme(project_dir,config)
    ok(f"Project '{name}' created at {project_dir}");return config

def _configure_bot(config,project_dir):
    section("Bot Configuration")
    btype=menu("Bot Platform",[
        ("1","Discord  — discord.py / py-cord"),
        ("2","Telegram — python-telegram-bot"),
        ("3","Slack    — slack-bolt"),
        ("4","Generic  — any Python script"),
    ])
    bmap={"1":"discord","2":"telegram","3":"slack","4":"generic"}
    bot_type=bmap.get(btype,"generic")
    (project_dir/"bot").mkdir(exist_ok=True)
    (project_dir/"bot_logs").mkdir(exist_ok=True)
    config["bot_type"]=bot_type
    config["bot_dir"]=str(project_dir/"bot")
    config["bot_entry"]=None
    config["bot_env"]={}
    config["bot_pip_deps"]=[]
    config["bot_status"]="stopped"
    if bot_type=="discord":
        tok=prompt("Discord Bot Token (blank to set later)","")
        if tok:config["bot_env"]["DISCORD_TOKEN"]=tok
        config["bot_pip_deps"]=["discord.py"]
    elif bot_type=="telegram":
        tok=prompt("Telegram Bot Token (blank to set later)","")
        if tok:config["bot_env"]["TELEGRAM_TOKEN"]=tok
        config["bot_pip_deps"]=["python-telegram-bot"]
    elif bot_type=="slack":
        tok=prompt("Slack Bot Token (blank to set later)","")
        sig=prompt("Slack Signing Secret (blank to set later)","")
        if tok:config["bot_env"]["SLACK_BOT_TOKEN"]=tok
        if sig:config["bot_env"]["SLACK_SIGNING_SECRET"]=sig
        config["bot_pip_deps"]=["slack-bolt"]
    extra=prompt("Extra pip packages (comma-separated or blank)","")
    if extra:config["bot_pip_deps"]+=[p.strip() for p in extra.split(",") if p.strip()]
    info("Upload your bot script via the admin panel after starting the server.")
    return config

def select_project():
    projects=list_projects()
    if not projects:warn("No projects found.");return None
    section("Load Existing Project")
    choice=menu("Select",([(str(i+1),p.name) for i,p in enumerate(projects)]))
    try:
        idx=int(choice)-1
        if 0<=idx<len(projects):
            cfg=load_config(projects[idx]);cfg["project_dir"]=str(projects[idx])
            ok(f"Loaded: {projects[idx].name}");return cfg
    except(ValueError,IndexError):pass
    err("Invalid selection.");return None

# ── SECTION 5: SECURITY + FILE UTILS ─────────────────────────────────────────
def safe_filename(filename):
    from werkzeug.utils import secure_filename
    n=secure_filename(filename)
    return (n or secrets.token_hex(8))[:200]

def safe_relpath(raw:str,base:Path)->Optional[Path]:
    """Validate a relative path (from folder upload or ZIP) against base dir."""
    clean=raw.replace("\\","/").lstrip("/")
    if not clean:return None
    parts=clean.split("/")
    # Reject traversal, empty components, and Windows drive letters
    if any(p==".." or p=="" or (len(p)==2 and p[1]==":") for p in parts):return None
    candidate=(base/clean).resolve()
    try:candidate.relative_to(base.resolve());return candidate
    except ValueError:return None

def prevent_path_traversal(base,target):
    try:target.resolve().relative_to(base.resolve());return True
    except ValueError:return False

def get_file_icon(fn):
    ext=Path(fn).suffix.lower()
    return {".html":"🌐",".htm":"🌐",".css":"🎨",".js":"⚙️",".mjs":"⚙️",
            ".json":"📋",".png":"🖼️",".jpg":"🖼️",".jpeg":"🖼️",".gif":"🖼️",
            ".svg":"🖼️",".webp":"🖼️",".ico":"🖼️",".woff":"🔤",".woff2":"🔤",
            ".ttf":"🔤",".eot":"🔤",".mp4":"🎬",".webm":"🎬",".mp3":"🎵",
            ".ogg":"🎵",".wav":"🎵",".pdf":"📄",".zip":"📦",".tar":"📦",
            ".gz":"📦",".txt":"📝",".md":"📝",".xml":"📋",".csv":"📋",
            ".py":"🐍",".rb":"💎",".php":"🐘"}.get(ext,"📄")

def format_size(b):
    if b<1024:return f"{b} B"
    if b<1048576:return f"{b/1024:.1f} KB"
    return f"{b/1048576:.1f} MB"


# ── LOGIN RATE LIMITING (in-memory, resets on restart) ──────────────────────
_login_attempts: Dict[str,List[float]] = {}  # ip -> [timestamps]
_LOGIN_MAX = 10          # max attempts
_LOGIN_WINDOW = 300      # seconds (5 min window)

def _rate_limit_check(ip: str) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    # Purge old attempts outside window
    attempts = [t for t in attempts if now - t < _LOGIN_WINDOW]
    _login_attempts[ip] = attempts
    return len(attempts) < _LOGIN_MAX

def _rate_limit_record(ip: str):
    """Record a failed login attempt."""
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts.append(now)
    _login_attempts[ip] = attempts

# ── CSRF PROTECTION (double-submit token, stateless) ─────────────────────────
def _csrf_token_for_session(secret_key: str, session_id: str) -> str:
    """Generate a CSRF token tied to the session. Uses HMAC-SHA256."""
    import hmac
    return hmac.new(secret_key.encode(), session_id.encode(), "sha256").hexdigest()[:32]

def _csrf_token(app_secret: str) -> str:
    """Get or create CSRF token stored in Flask session."""
    from flask import session as _sess
    if "_csrf" not in _sess:
        _sess["_csrf"] = secrets.token_hex(16)
    return _sess["_csrf"]

def _csrf_validate(app_secret: str) -> bool:
    """Return True if request CSRF token matches session token."""
    from flask import session as _sess, request as _req
    expected = _sess.get("_csrf")
    if not expected:
        return False
    submitted = _req.form.get("_csrf_token","") or _req.headers.get("X-CSRF-Token","")
    return secrets.compare_digest(expected, submitted)


# ── SECTION 6: DESIGN SYSTEM (CSS + JS) ──────────────────────────────────────
_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#080c10;--surface:#0d1219;--surface2:#131a24;--border:#1e2d3d;--border2:#243447;
  --text:#cdd9e5;--muted:#546e7a;--accent:#00d4aa;--accent2:#0097ff;--warn:#f5a623;
  --danger:#f04f4f;--success:#00c87a;--radius:10px;--radius-sm:6px;
  --font:'Syne',system-ui,sans-serif;--mono:'JetBrains Mono','Courier New',monospace;
  --glow:0 0 20px rgba(0,212,170,.12);--glow2:0 0 20px rgba(0,151,255,.12)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);min-height:100vh;line-height:1.5}
.layout{display:grid;grid-template-columns:240px 1fr;min-height:100vh}
.sidebar{background:var(--surface);border-right:1px solid var(--border);display:flex;
  flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto}
.sidebar-logo{padding:1.5rem 1.25rem 1rem;border-bottom:1px solid var(--border)}
.wm{font-size:1.3rem;font-weight:800;color:var(--accent);letter-spacing:-.02em;display:block}
.sub{font-size:.7rem;color:var(--muted);font-family:var(--mono);margin-top:.15rem}
.nav-section{padding:.75rem 1rem .25rem;font-size:.65rem;font-weight:700;letter-spacing:.12em;
  color:var(--muted);text-transform:uppercase}
.nav-item{display:flex;align-items:center;gap:.6rem;padding:.55rem 1.25rem;color:var(--muted);
  text-decoration:none;font-size:.875rem;font-weight:600;border-left:3px solid transparent;transition:all .15s}
.nav-item:hover{color:var(--text);background:var(--surface2)}
.nav-item.active{color:var(--accent);border-left-color:var(--accent);background:rgba(0,212,170,.06)}
.sidebar-footer{margin-top:auto;padding:1rem 1.25rem;border-top:1px solid var(--border);
  font-size:.7rem;color:var(--muted);font-family:var(--mono)}
.main{padding:2rem 2.5rem;min-width:0}
.page-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:2rem;gap:1rem}
.page-title{font-size:1.6rem;font-weight:800;color:var(--text);letter-spacing:-.03em}
.page-sub{color:var(--muted);font-size:.85rem;margin-top:.25rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem;margin-bottom:1.5rem}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;gap:1rem}
.card-title{font-size:1rem;font-weight:700;color:var(--text)}
.card-sub{font-size:.8rem;color:var(--muted);margin-top:.15rem}
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem;margin-bottom:1.5rem}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.25rem;position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2))}
.stat-value{font-size:1.8rem;font-weight:800;color:var(--text);line-height:1}
.stat-label{font-size:.75rem;color:var(--muted);margin-top:.4rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.07em}
.badge{display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .65rem;
  border-radius:100px;font-size:.7rem;font-weight:700;font-family:var(--mono)}
.bg{background:rgba(0,200,122,.12);color:var(--success);border:1px solid rgba(0,200,122,.25)}
.bb{background:rgba(0,151,255,.12);color:var(--accent2);border:1px solid rgba(0,151,255,.25)}
.bw{background:rgba(245,166,35,.12);color:var(--warn);border:1px solid rgba(245,166,35,.25)}
.br{background:rgba(240,79,79,.12);color:var(--danger);border:1px solid rgba(240,79,79,.25)}
.bm{background:rgba(84,110,122,.12);color:var(--muted);border:1px solid rgba(84,110,122,.25)}
.ba{background:rgba(0,212,170,.12);color:var(--accent);border:1px solid rgba(0,212,170,.25)}
.sdot{width:6px;height:6px;border-radius:50%;display:inline-block;background:currentColor}
.btn{display:inline-flex;align-items:center;gap:.4rem;padding:.55rem 1.1rem;
  border-radius:var(--radius-sm);font-size:.82rem;font-weight:700;cursor:pointer;
  border:1px solid transparent;font-family:var(--font);text-decoration:none;transition:all .15s;white-space:nowrap}
.btn-p{background:var(--accent);color:#000}.btn-p:hover{opacity:.88;box-shadow:var(--glow)}
.btn-b{background:var(--accent2);color:#fff}.btn-b:hover{opacity:.88;box-shadow:var(--glow2)}
.btn-o{background:transparent;color:var(--text);border-color:var(--border2)}
.btn-o:hover{background:var(--surface2);border-color:var(--accent);color:var(--accent)}
.btn-d{background:rgba(240,79,79,.12);color:var(--danger);border-color:rgba(240,79,79,.3)}
.btn-d:hover{background:var(--danger);color:#fff}
.btn-w{background:rgba(245,166,35,.12);color:var(--warn);border-color:rgba(245,166,35,.3)}
.btn-w:hover{background:var(--warn);color:#000}
.btn-g{background:rgba(0,200,122,.12);color:var(--success);border-color:rgba(0,200,122,.3)}
.btn-g:hover{background:var(--success);color:#000}
.btn-sm{padding:.35rem .7rem;font-size:.75rem}.btn-lg{padding:.75rem 1.6rem;font-size:.95rem}
/* Upload tabs */
.upload-tabs{display:flex;gap:0;margin-bottom:1rem;border:1px solid var(--border2);
  border-radius:var(--radius-sm);overflow:hidden;width:fit-content}
.upload-tab{padding:.5rem 1.25rem;font-size:.8rem;font-weight:700;cursor:pointer;
  background:transparent;color:var(--muted);border:none;font-family:var(--font);transition:all .15s}
.upload-tab.active{background:var(--accent);color:#000}
.upload-tab:hover:not(.active){background:var(--surface2);color:var(--text)}
.upload-pane{display:none}.upload-pane.active{display:block}
.upload-zone{border:2px dashed var(--border2);border-radius:var(--radius);padding:3rem 2rem;
  text-align:center;cursor:pointer;transition:all .2s;background:var(--surface2);position:relative}
.upload-zone:hover,.upload-zone.drag-over{border-color:var(--accent);background:rgba(0,212,170,.04);box-shadow:var(--glow)}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.upload-icon{font-size:2.5rem;margin-bottom:.75rem;display:block}
.upload-label{font-size:1rem;font-weight:700;color:var(--text)}
.upload-sub{font-size:.8rem;color:var(--muted);margin-top:.35rem}
.file-preview{margin-top:.75rem;max-height:160px;overflow-y:auto;
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:.5rem .75rem;font-family:var(--mono);font-size:.72rem;color:var(--muted);text-align:left;display:none}
.file-preview div{padding:.15rem 0;border-bottom:1px solid var(--border)}
.file-preview div:last-child{border:none}
/* File table */
.ft{width:100%;border-collapse:collapse}
.ft th{text-align:left;padding:.6rem .9rem;font-size:.72rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;color:var(--muted);border-bottom:1px solid var(--border);background:var(--surface2)}
.ft td{padding:.7rem .9rem;border-bottom:1px solid var(--border);font-size:.85rem;vertical-align:middle}
.ft tr:last-child td{border-bottom:none}.ft tr:hover td{background:rgba(255,255,255,.02)}
.fname{display:flex;align-items:center;gap:.5rem;font-weight:600;color:var(--text);font-family:var(--mono);font-size:.78rem}
.fpath{color:var(--muted);font-family:var(--mono);font-size:.7rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:240px}
.fmeta{color:var(--muted);font-family:var(--mono);font-size:.75rem}
.actions{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
/* Hosting banner */
.hosting-banner{background:linear-gradient(135deg,rgba(0,212,170,.08),rgba(0,151,255,.08));
  border:1px solid rgba(0,212,170,.25);border-radius:var(--radius);padding:1.25rem 1.5rem;
  margin-bottom:1.5rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.hb-left{display:flex;align-items:center;gap:.75rem}
.hb-label{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.hb-url{font-family:var(--mono);font-size:.9rem;color:var(--accent);font-weight:600;margin-top:.15rem;word-break:break-all}
.pulse{width:10px;height:10px;border-radius:50%;background:var(--accent);flex-shrink:0;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,212,170,.5)}50%{box-shadow:0 0 0 8px rgba(0,212,170,0)}}
/* Alerts */
.alert{padding:.8rem 1rem;border-radius:var(--radius-sm);font-size:.85rem;margin-bottom:1rem;display:flex;align-items:flex-start;gap:.6rem}
.ao{background:rgba(0,200,122,.1);color:var(--success);border:1px solid rgba(0,200,122,.25)}
.ae{background:rgba(240,79,79,.1);color:var(--danger);border:1px solid rgba(240,79,79,.25)}
.ai{background:rgba(0,151,255,.1);color:var(--accent2);border:1px solid rgba(0,151,255,.25)}
.aw{background:rgba(245,166,35,.1);color:var(--warn);border:1px solid rgba(245,166,35,.25)}
/* Login */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;background:var(--bg)}
.login-card{width:100%;max-width:380px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:2.5rem 2rem}
.login-logo{font-size:1.6rem;font-weight:800;color:var(--accent);margin-bottom:.25rem}
.login-sub{color:var(--muted);font-size:.8rem;margin-bottom:2rem}
label.fl{display:block;font-size:.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.4rem}
input[type=text],input[type=password],input[type=file],select,textarea{
  background:var(--surface2);border:1px solid var(--border2);border-radius:var(--radius-sm);
  color:var(--text);padding:.6rem .85rem;width:100%;font-size:.875rem;font-family:var(--font);
  outline:none;margin-bottom:1rem;transition:border-color .15s}
input:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,212,170,.12)}
.empty-state{text-align:center;padding:3rem 1rem;color:var(--muted)}
.empty-icon{font-size:3rem;display:block;margin-bottom:1rem;opacity:.4}
.mono{font-family:var(--mono);font-size:.8rem;color:var(--accent)}
.progress{height:4px;background:var(--border);border-radius:2px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px;transition:width .3s}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
@media(max-width:768px){.layout{grid-template-columns:1fr}.main{padding:1.25rem}}
.w-full{width:100%}.truncate{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:280px}
.bot-terminal{background:#000;border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:1rem;font-family:var(--mono);font-size:.75rem;color:#00ff88;
  height:320px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
.env-row{display:grid;grid-template-columns:1fr 1fr auto;gap:.5rem;margin-bottom:.5rem;align-items:center}
</style>"""

_JS = """<script>
// Populate CSRF tokens on page load
fetch('/api/csrf').then(r=>r.json()).then(d=>{
  document.querySelectorAll('input[name=_csrf_token]').forEach(i=>i.value=d.token);
}).catch(()=>{});

// Upload tabs
function initTabs(group){
  group.querySelectorAll('.upload-tab').forEach(tab=>{
    tab.addEventListener('click',()=>{
      group.querySelectorAll('.upload-tab').forEach(t=>t.classList.remove('active'));
      group.querySelectorAll('.upload-pane').forEach(p=>p.classList.remove('active'));
      tab.classList.add('active');
      const pane=group.querySelector('#pane-'+tab.dataset.pane);
      if(pane)pane.classList.add('active');
    });
  });
}
document.querySelectorAll('.upload-tab-group').forEach(initTabs);

// File input → preview
function _fmtSize(b){if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB';}
document.querySelectorAll('input[type=file]').forEach(inp=>{
  inp.addEventListener('change',()=>{
    const zone=inp.closest('.upload-zone');if(!zone)return;
    const label=zone.querySelector('.upload-label');
    const preview=zone.querySelector('.file-preview');
    const files=Array.from(inp.files);
    if(label){label.textContent=files.length===1?files[0].name:files.length+' files selected';}
    if(preview&&files.length){
      preview.style.display='block';
      preview.innerHTML=files.slice(0,80).map(f=>{
        const rel=f.webkitRelativePath||f.name;
        return '<div>'+rel+' <span style="opacity:.5">('+_fmtSize(f.size)+')</span></div>';
      }).join('')+(files.length>80?'<div style="color:var(--accent)">…and '+(files.length-80)+' more</div>':'');
    }
  });
});

// Drag-drop
document.querySelectorAll('.upload-zone').forEach(zone=>{
  zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over');});
  zone.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
  zone.addEventListener('drop',e=>{
    e.preventDefault();zone.classList.remove('drag-over');
    const inp=zone.querySelector('input[type=file]');
    if(!inp||!e.dataTransfer.files.length)return;
    // Folder inputs block programmatic .files assignment (browser security restriction)
    if(inp.hasAttribute('webkitdirectory')){
      const label=zone.querySelector('.upload-label');
      if(label)label.textContent='Folder drag-drop not supported — click to select folder';
      return;
    }
    // Transfer dropped files into the input so the form actually submits them
    try{
      const dt=new DataTransfer();
      Array.from(e.dataTransfer.files).forEach(f=>dt.items.add(f));
      inp.files=dt.files;
      inp.dispatchEvent(new Event('change'));
    }catch(err){
      const label=zone.querySelector('.upload-label');
      if(label)label.textContent=e.dataTransfer.files.length+' file(s) dropped — click Upload';
    }
  });
});

function copyText(text,btn){
  navigator.clipboard.writeText(text).then(()=>{
    const o=btn.textContent;btn.textContent='✓ Copied';setTimeout(()=>btn.textContent=o,1800);
  });
}

// Upload progress animation (each form has a unique data-upload="files|folder|zip")
document.querySelectorAll('form[data-upload]').forEach(form=>{
  form.addEventListener('submit',()=>{
    const pane=form.dataset.upload;
    const bar=document.getElementById('upload-progress-'+pane);
    if(bar){bar.style.display='block';let w=0;
      setInterval(()=>{w=Math.min(w+Math.random()*12,88);bar.querySelector('.progress-fill').style.width=w+'%';},150);
    }
  });
});

// Auto-dismiss ok/info alerts
setTimeout(()=>{
  document.querySelectorAll('.ao,.ai').forEach(el=>{
    el.style.transition='opacity .4s';el.style.opacity='0';setTimeout(()=>el.remove(),400);
  });
},4500);

// Confirm links
document.querySelectorAll('[data-confirm]').forEach(el=>{
  el.addEventListener('click',e=>{if(!confirm(el.dataset.confirm))e.preventDefault();});
});

// Env var rows
function addEnvRow(){
  const c=document.getElementById('env-container');
  const d=document.createElement('div');d.className='env-row';
  d.innerHTML='<input type="text" name="env_key[]" placeholder="KEY" style="margin:0">'
    +'<input type="text" name="env_val[]" placeholder="value" style="margin:0">'
    +'<button type="button" class="btn btn-d btn-sm" onclick="this.closest(\'.env-row\').remove()">✕</button>';
  c.appendChild(d);
}

// Bot terminal live poll
const termEl=document.getElementById('bot-terminal');
if(termEl){
  termEl.scrollTop=termEl.scrollHeight;
  setInterval(()=>{
    fetch('/admin/bot/logs-raw').then(r=>r.text()).then(t=>{termEl.textContent=t;termEl.scrollTop=termEl.scrollHeight;}).catch(()=>{});
  },3000);
}
</script>"""

# ── SECTION 7: PAGE HELPERS ───────────────────────────────────────────────────
def _alert(msg,kind="ok"):
    if not msg:return ""
    cls={"ok":"ao","err":"ae","info":"ai","warn":"aw"}.get(kind,"ai")
    icon={"ok":"✓","err":"✖","info":"ℹ","warn":"⚠"}.get(kind,"ℹ")
    return f'<div class="alert {cls}">{icon} {msg}</div>'

def _shell(title,body,nav_active,project_name,extra_nav="",hosted=None,pub_url=None):
    def _n(href,ic,lb,k):
        cls="nav-item active" if nav_active==k else "nav-item"
        return f'<a href="{href}" class="{cls}"><span style="width:16px;text-align:center;flex-shrink:0">{ic}</span>{lb}</a>'
    banner_html=""
    if pub_url:
        banner_html=(f'<div class="hosting-banner"><div class="hb-left"><div class="pulse"></div>'
                     f'<div><div class="hb-label">Live Public URL</div>'
                     f'<div class="hb-url">{_html.escape(str(pub_url))}</div></div></div>'
                     f'<div style="display:flex;gap:.5rem">'
                     f'<button class="btn btn-o btn-sm" onclick="copyText(\'{pub_url}\',this)">📋 Copy</button>'
                     f'<a href="{pub_url}" target="_blank" class="btn btn-p btn-sm">↗ Open</a>'
                     f'</div></div>')
    elif hosted:
        banner_html=(f'<div class="hosting-banner" style="background:rgba(245,166,35,.06);border-color:rgba(245,166,35,.25)">'
                     f'<div class="hb-left">'
                     f'<div style="width:10px;height:10px;border-radius:50%;background:var(--warn);flex-shrink:0"></div>'
                     f'<div><div class="hb-label">Hosted Locally</div>'
                     f'<div class="hb-url" style="color:var(--warn)">Serving: {_html.escape(str(hosted))} · No public tunnel</div></div></div>'
                     f'<a href="/admin/tunnel" class="btn btn-w btn-sm">🌐 Get Public URL</a></div>')
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title} — Serta</title>{_CSS}</head><body>'
            f'<div class="layout"><aside class="sidebar">'
            f'<div class="sidebar-logo"><span class="wm">⚡ Serta</span>'
            f'<span class="sub">{_html.escape(str(project_name))}</span></div>'
            f'<div class="nav-section">Navigation</div>'
            f'{extra_nav}'
            f'<div class="nav-section" style="margin-top:.5rem">Account</div>'
            f'{_n("/admin/logout","🚪","Logout","logout")}'
            f'<div class="sidebar-footer">Serta v3.2</div>'
            f'</aside><main class="main">{banner_html}{body}</main></div>{_JS}</body></html>')

def _login_page(error="",action="/admin/login"):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Login — Serta</title>{_CSS}</head><body>'
            f'<div class="login-wrap"><div class="login-card">'
            f'<div class="login-logo">⚡ Serta</div>'
            f'<div class="login-sub">Server Creation &amp; Automation</div>'
            f'{_alert(error,"err") if error else ""}'
            f'<form method="POST" action="{action}">'
            f'<label class="fl">Password</label>'
            f'<input type="hidden" name="_csrf_token" value="">'  # filled by JS below
    f'<input type="password" name="password" placeholder="Enter admin password" autofocus required>'
            f'<button type="submit" class="btn btn-p w-full btn-lg">Login →</button>'
    f'<script>fetch("/api/csrf").then(r=>r.json()).then(d=>{{document.querySelector("input[name=_csrf_token]").value=d.token}}).catch(()=>{{}})</script>'
            f'</form></div></div>{_JS}</body></html>')

# ── SECTION 8: UPLOAD WIDGET HTML ────────────────────────────────────────────
def _upload_widget(action_url, hint="", csrf_tok=""):
    """
    Three-tab upload widget: Files | Folder | ZIP
    Browser sends webkitRelativePath as part of filename for folder uploads.
    All submit to action_url, field name 'files', hidden field 'upload_mode'.

    csrf_tok must be passed server-side so the token is inlined in the HTML —
    never rely on an async JS fetch to populate CSRF fields before submission.
    """
    return f"""
<div class="upload-tab-group">
  <div class="upload-tabs">
    <button type="button" class="upload-tab active" data-pane="files">📄 Files</button>
    <button type="button" class="upload-tab" data-pane="folder">📁 Folder</button>
    <button type="button" class="upload-tab" data-pane="zip">📦 ZIP</button>
  </div>
  <div class="upload-pane active" id="pane-files">
    <form method="POST" action="{action_url}" enctype="multipart/form-data" data-upload="files">
      <input type="hidden" name="upload_mode" value="files">
      <input type="hidden" name="_csrf_token" value="{csrf_tok}">
      <div class="upload-zone">
        <input type="file" name="files" multiple>
        <span class="upload-icon">☁</span>
        <div class="upload-label">Drop files or click to browse</div>
        <div class="upload-sub">{hint}</div>
        <div class="file-preview"></div>
      </div>
      <div id="upload-progress-files" style="display:none;margin-top:.75rem">
        <div class="progress"><div class="progress-fill" style="width:0%"></div></div>
      </div>
      <div style="margin-top:1rem;display:flex;gap:.75rem">
        <button type="submit" class="btn btn-p btn-lg">Upload Files</button>
      </div>
    </form>
  </div>
  <div class="upload-pane" id="pane-folder">
    <form method="POST" action="{action_url}" enctype="multipart/form-data" data-upload="folder">
      <input type="hidden" name="upload_mode" value="folder">
      <input type="hidden" name="_csrf_token" value="{csrf_tok}">
      <div class="upload-zone">
        <input type="file" name="files" multiple webkitdirectory mozdirectory>
        <span class="upload-icon">📂</span>
        <div class="upload-label">Click to select a folder</div>
        <div class="upload-sub">Full directory tree is uploaded &amp; preserved on server</div>
        <div class="file-preview"></div>
      </div>
      <div id="upload-progress-folder" style="display:none;margin-top:.75rem">
        <div class="progress"><div class="progress-fill" style="width:0%"></div></div>
      </div>
      <div style="margin-top:1rem">
        <button type="submit" class="btn btn-p btn-lg">Upload Folder</button>
      </div>
    </form>
  </div>
  <div class="upload-pane" id="pane-zip">
    <form method="POST" action="{action_url}" enctype="multipart/form-data" data-upload="zip">
      <input type="hidden" name="upload_mode" value="zip">
      <input type="hidden" name="_csrf_token" value="{csrf_tok}">
      <div class="upload-zone">
        <input type="file" name="files" accept=".zip">
        <span class="upload-icon">📦</span>
        <div class="upload-label">Drop a ZIP archive</div>
        <div class="upload-sub">Extracted preserving folder structure</div>
        <div class="file-preview"></div>
      </div>
      <div id="upload-progress-zip" style="display:none;margin-top:.75rem">
        <div class="progress"><div class="progress-fill" style="width:0%"></div></div>
      </div>
      <div style="margin-top:1rem">
        <button type="submit" class="btn btn-p btn-lg">Extract &amp; Upload</button>
      </div>
    </form>
  </div>
</div>"""

# ── SECTION 9: UPLOAD PROCESSOR (server-side, shared by all server types) ────
def process_upload(files_field: list, dest_base: Path, allowed_ext: set, upload_mode: str = ""):
    """
    Save uploaded files to dest_base.

    upload_mode: "files" | "folder" | "zip" (from hidden form field).
    For folder uploads: browsers send webkitRelativePath embedded in filename.
    We strip the first path component, then recreate the tree under dest_base.
    For flat file uploads: save directly in dest_base.
    For ZIP: extract preserving internal structure.

    Returns (saved: list[str], errors: list[str])
    """
    import io as _io
    saved, errors = [], []
    if not files_field:
        return saved, errors  # Nothing to process

    def _allowed(fname):
        return "." in fname and fname.rsplit(".",1)[1].lower() in allowed_ext

    def _dedup(p:Path)->Path:
        if not p.exists():return p
        stem=p.stem;suf=p.suffix;i=1
        while True:
            q=p.parent/f"{stem}_{i}{suf}"
            if not q.exists():return q
            i+=1

    def _save(data:bytes, relpath_str:str):
        """Save bytes to dest_base/relpath_str (creating subdirs)."""
        dest=safe_relpath(relpath_str,dest_base)
        if dest is None:
            errors.append(f"Blocked (traversal): {relpath_str}");return
        if not _allowed(dest.name):
            errors.append(f"Type not allowed: {dest.name}");return
        dest=_dedup(dest)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
        saved.append(str(dest.relative_to(dest_base)).replace("\\","/"))

    def _extract_zip(data:bytes):
        try:
            with zipfile.ZipFile(_io.BytesIO(data)) as zf:
                for m in zf.infolist():
                    if m.filename.endswith("/"):continue
                    parts=Path(m.filename.replace("\\","/")).parts
                    # Strip top-level folder if present (common in GitHub zips)
                    rel="/".join(parts[1:]) if len(parts)>1 else parts[0]
                    fname=Path(rel).name
                    if fname.startswith(".") or fname.startswith("__"):continue
                    with zf.open(m) as src:_save(src.read(),rel)
        except zipfile.BadZipFile:
            errors.append("Invalid ZIP file.")

    for f in files_field:
        if not f or not f.filename:continue
        raw=f.filename.replace("\\","/")

        # ZIP passthrough (also handles upload_mode==zip)
        if raw.lower().endswith(".zip"):
            try:f.seek(0)
            except (AttributeError,OSError):pass
            _extract_zip(f.read());continue

        # Folder upload: use explicit upload_mode when available;
        # fall back to path-separator detection (webkitRelativePath embedded in filename)
        if upload_mode=="folder" or ("/" in raw and upload_mode!="files"):
            parts=raw.split("/")
            # Skip hidden / system paths
            if any(p.startswith(".") or p.startswith("__") for p in parts):continue
            # Strip the root folder name (first component)
            rel="/".join(parts[1:]) if len(parts)>1 else parts[0]
            if not rel or rel.endswith("/"):continue  # skip bare folder entries
            try:f.seek(0)
            except (AttributeError,OSError):pass
            _save(f.read(),rel)
        else:
            # Flat file upload
            fname=safe_filename(raw)
            if not fname:errors.append("Invalid filename.");continue
            if not _allowed(fname):errors.append(f"Type not allowed: {fname}");continue
            dest=_dedup(dest_base/fname)
            if not prevent_path_traversal(dest_base,dest):
                errors.append(f"Blocked: {fname}");continue
            try:f.seek(0)
            except (AttributeError,OSError):pass
            dest.write_bytes(f.read())
            saved.append(fname)

    return saved,errors

# ── SECTION 10: WEB SERVER ────────────────────────────────────────────────────
_WEB_ALLOWED={
    "html","htm","css","js","mjs","json","svg","png","jpg","jpeg","gif","webp",
    "ico","woff","woff2","ttf","eot","otf","mp4","webm","mp3","ogg","wav",
    "txt","md","xml","csv","zip",
}

def build_web_server(config:Dict[str,Any],runtime_ref=None):
    from flask import Flask,request,redirect,session,send_file as sf,abort,jsonify

    project_dir=Path(config["project_dir"])
    site_dir=Path(config.get("site_dir",str(project_dir/"site")))
    site_dir.mkdir(parents=True,exist_ok=True)
    pw_hash=config.get("admin_password_hash",_hash_password("admin"))

    app=Flask(__name__)
    app.secret_key=config.get("secret_key",secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"]=True
    app.config["SESSION_COOKIE_SAMESITE"]="Lax"
    app.config["MAX_CONTENT_LENGTH"]=256*1024*1024
    _setup_logging(app,project_dir)

    def is_admin():return session.get("admin_authed",False)
    def gate():
        if not is_admin():return redirect("/admin/login")
        return None
    def pub_url():return runtime_ref.public_url if runtime_ref else None
    def tun_active():return runtime_ref is not None and runtime_ref.tunnel_proc is not None

    def get_tree():
        result=[]
        for p in sorted(site_dir.rglob("*")):
            # Only filter hidden parts relative to site_dir, not absolute path ancestors
            rel_parts=p.relative_to(site_dir).parts
            if any(part.startswith(".") or part.startswith("__") for part in rel_parts):continue
            stat=p.stat()
            result.append({"relpath":str(p.relative_to(site_dir)).replace("\\","/"),
                           "name":p.name,"is_dir":p.is_dir(),
                           "size":stat.st_size if p.is_file() else 0,
                           "modified":datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")})
        return result

    def read_logs():
        lf=project_dir/"logs"/"server.log"
        return lf.read_text(errors="replace").splitlines() if lf.exists() else []

    def _nav(active):
        def _n(href,ic,lb,k):
            cls="nav-item active" if active==k else "nav-item"
            return f'<a href="{href}" class="{cls}"><span style="width:16px;text-align:center;flex-shrink:0">{ic}</span>{lb}</a>'
        return (_n("/admin","📁","File Manager","files")+
                _n("/admin/upload","📤","Upload","upload")+
                _n("/admin/hosting","🌐","Hosting","hosting")+
                _n("/admin/tunnel","🚇","Public Tunnel","tunnel")+
                '<div class="nav-section" style="margin-top:.5rem">Website</div>'+
                _n("/","👁","View Live Site","preview")+
                _n("/admin/logs","📋","Logs","logs"))

    def page(title,body,active,flash_msg=None,flash_type=None):
        return _shell(title,_alert(flash_msg,flash_type)+body,active,
                      config.get("name","serta"),_nav(active),
                      hosted=config.get("hosted_entry"),pub_url=pub_url())

    # Public routes
    @app.route("/")
    def index():
        entry=config.get("hosted_entry")
        if entry:
            target=(site_dir/entry).resolve()
            if target.exists() and prevent_path_traversal(site_dir,target):
                return sf(str(target))
        return ("<!DOCTYPE html><html><head><meta charset=UTF-8><title>Serta</title></head>"
                "<body style='display:flex;align-items:center;justify-content:center;min-height:100vh;"
                "background:#080c10;color:#cdd9e5;font-family:sans-serif;flex-direction:column;gap:1rem'>"
                "<div style='font-size:3rem'>⚡</div>"
                "<h1 style='color:#00d4aa;font-weight:800'>Serta Web Server</h1>"
                "<p style='color:#546e7a'>No site hosted. "
                "<a href='/admin' style='color:#0097ff'>Admin Panel →</a></p>"
                "</body></html>")

    @app.route("/<path:filename>")
    def serve_any(filename):
        # Don't intercept admin routes (exact match or sub-path)
        if filename == "admin" or filename.startswith("admin/"):abort(404)
        target=(site_dir/filename).resolve()
        if not prevent_path_traversal(site_dir,target) or not target.exists():abort(404)
        if target.is_dir():
            idx=target/"index.html"
            if idx.exists():target=idx
            else:abort(404)
        mime=mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        return sf(str(target),mimetype=mime)

    # Admin auth
    @app.route("/admin/login",methods=["GET","POST"])
    def admin_login():
        if request.method=="POST":
            ip=request.remote_addr or "unknown"
            if not _rate_limit_check(ip):
                return _login_page("Too many attempts. Wait 5 minutes."),429
            if not _csrf_validate(app.secret_key):
                return _login_page("Request validation failed. Please try again."),403
            if check_password(request.form.get("password",""),pw_hash):
                session["admin_authed"]=True;return redirect("/admin")
            _rate_limit_record(ip)
            return _login_page("Incorrect password."),401
        _csrf_token(app.secret_key)
        return _login_page()

    @app.route("/admin/logout")
    def admin_logout():session.clear();return redirect("/admin/login")

    # File manager
    @app.route("/admin")
    @app.route("/admin/")
    def admin_index():
        g=gate()
        if g:return g
        # Read optional flash from redirect (e.g. after upload success)
        flash_msg=request.args.get("msg")
        flash_type=request.args.get("mt","ok")
        tree=get_tree();files=[f for f in tree if not f["is_dir"]]
        hosted=config.get("hosted_entry")
        total=sum(f["size"] for f in files);hcount=sum(1 for f in files if f["name"].endswith((".html",".htm")))
        stats=(f'<div class="stats-row">'
               f'<div class="stat-card"><div class="stat-value">{len(files)}</div><div class="stat-label">Files</div></div>'
               f'<div class="stat-card"><div class="stat-value">{hcount}</div><div class="stat-label">HTML</div></div>'
               f'<div class="stat-card"><div class="stat-value">{format_size(total)}</div><div class="stat-label">Size</div></div>'
               f'<div class="stat-card"><div class="stat-value">{"🟢" if hosted else "🔴"}</div><div class="stat-label">{"Live" if hosted else "No Host"}</div></div>'
               f'</div>')
        if not files:
            table='<div class="empty-state"><span class="empty-icon">📂</span><p>No files yet. <a href="/admin/upload" style="color:var(--accent)">Upload →</a></p></div>'
        else:
            rows=""
            for f in files:
                fn=f["relpath"];icon=get_file_icon(f["name"]);is_host=(hosted==fn)
                folder=str(Path(fn).parent) if "/" in fn else ""
                fhint=f'<div class="fpath">📁 {folder}</div>' if folder else ""
                hbtn=""
                if f["name"].lower().endswith((".html",".htm")):
                    if is_host:hbtn='<a href="/admin/unhost" class="btn btn-w btn-sm">⏹ Stop</a>'
                    else:hbtn=f'<a href="/admin/host/{fn}" class="btn btn-b btn-sm">▶ Host</a>'
                badge='<span class="badge bg"><span class="sdot"></span> LIVE</span>' if is_host else ""
                rows+=(f'<tr><td><div class="fname"><span>{icon}</span>'
                       f'<div><div class="truncate">{f["name"]}</div>{fhint}</div>{badge}</div></td>'
                       f'<td class="fmeta">{format_size(f["size"])}</td>'
                       f'<td class="fmeta">{f["modified"]}</td>'
                       f'<td><div class="actions">{hbtn}'
                       f'<a href="/admin/preview/{fn}" target="_blank" class="btn btn-o btn-sm">👁</a>'
                       f'<a href="/admin/dl/{fn}" class="btn btn-o btn-sm">⬇</a>'
                       f'<a href="/admin/delete/{fn}" class="btn btn-d btn-sm" data-confirm="Delete {f["name"]}?">🗑</a>'
                       f'</div></td></tr>')
            table=(f'<table class="ft"><thead><tr><th>File</th><th>Size</th><th>Modified</th><th>Actions</th></tr></thead>'
                   f'<tbody>{rows}</tbody></table>')
        body=(f'<div class="page-header"><div><div class="page-title">📁 File Manager</div>'
              f'<div class="page-sub">Full folder structure preserved — subdirectory files served at their path</div></div>'
              f'<a href="/admin/upload" class="btn btn-p">+ Upload</a></div>'
              f'{stats}<div class="card"><div class="card-header"><div>'
              f'<div class="card-title">Site Files</div>'
              f'<div class="card-sub">▶ Host any HTML file to serve it as the root page</div>'
              f'</div></div>{table}</div>')
        return page("File Manager",body,"files",flash_msg,flash_type)

    # Upload
    @app.route("/admin/upload",methods=["GET","POST"])
    def admin_upload():
        g=gate()
        if g:return g
        if request.method=="POST":
            if not _csrf_validate(app.secret_key):
                return _render_upload("Request validation failed. Refresh and try again.","err"),403
            mode=request.form.get("upload_mode","files")
            flist=request.files.getlist("files")
            mode=request.form.get("upload_mode","")
            saved,errors=process_upload(flist,site_dir,_WEB_ALLOWED,mode)
            if saved and not errors:
                return redirect(f"/admin?msg={len(saved)}+file(s)+uploaded&mt=ok")
            elif saved:
                msg=f"Uploaded {len(saved)} | Errors: {'; '.join(errors[:3])}";return _render_upload(msg,"warn")
            else:
                return _render_upload("Failed: "+"; ".join(errors[:5]),"err")
        return _render_upload()

    def _render_upload(flash_msg=None,flash_type=None):
        widget=_upload_widget("/admin/upload","HTML · CSS · JS · Images · Fonts · ZIP",_csrf_token(app.secret_key))
        body=(f'<div class="page-header"><div><div class="page-title">📤 Upload</div>'
              f'<div class="page-sub">Files, entire folders, or ZIP archives — structure preserved</div></div></div>'
              f'<div class="card"><div class="card-header"><div>'
              f'<div class="card-title">Upload to Site</div>'
              f'<div class="card-sub">Folder uploads recreate the full directory tree on the server</div>'
              f'</div></div>{widget}</div>')
        return page("Upload",body,"upload",flash_msg,flash_type)

    # Host / Unhost
    @app.route("/admin/host/<path:relpath>")
    def admin_host(relpath):
        g=gate()
        if g:return g
        target=(site_dir/relpath).resolve()
        if not prevent_path_traversal(site_dir,target) or not target.exists():
            return redirect("/admin")
        if not target.name.lower().endswith((".html",".htm")):
            return redirect("/admin")
        config["hosted_entry"]=relpath
        save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    @app.route("/admin/unhost")
    def admin_unhost():
        g=gate()
        if g:return g
        config["hosted_entry"]=None;save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    # Hosting page
    @app.route("/admin/hosting")
    def admin_hosting():
        g=gate()
        if g:return g
        hosted=config.get("hosted_entry");port=config.get("port",5000)
        if hosted:
            hs=(f'<div class="alert ao">✓ Serving: <strong class="mono">{hosted}</strong></div>'
                f'<div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:1.5rem">'
                f'<a href="/" target="_blank" class="btn btn-p">↗ View Site</a>'
                f'<a href="/admin/unhost" class="btn btn-d">⏹ Stop</a></div>')
        else:
            hs=('<div class="alert aw">⚠ No file hosted. Click ▶ Host in File Manager.</div>'
                '<a href="/admin" class="btn btn-b" style="margin-bottom:1.5rem">File Manager →</a>')
        pu=pub_url()
        pub_badge="bg" if pu else "bm"
        pub_cell=f'<a href="/admin/tunnel" class="btn btn-o btn-sm">Start →</a>' if not pu else ""
        body=(f'<div class="page-header"><div><div class="page-title">🌐 Hosting</div></div></div>'
              f'{hs}<div class="card"><div class="card-title" style="margin-bottom:.75rem">URLs</div>'
              f'<table class="ft"><thead><tr><th>Type</th><th>URL</th><th></th></tr></thead><tbody>'
              f'<tr><td><span class="badge ba">Local</span></td>'
              f'<td class="mono">http://127.0.0.1:{port}</td>'
              f'<td><button class="btn btn-o btn-sm" onclick="copyText(\'http://127.0.0.1:{port}\',this)">📋</button></td></tr>'
              f'<tr><td><span class="badge {pub_badge}">Public</span></td>'
              f'<td class="mono">{pu or "— No tunnel active"}</td>'
              f'<td>{pub_cell}</td></tr>'
              f'</tbody></table></div>')
        return page("Hosting",body,"hosting")

    # Tunnel
    @app.route("/admin/tunnel")
    def admin_tunnel():
        g=gate()
        if g:return g
        port=config.get("port",5000);pu=pub_url()
        if tun_active() and pu:
            sec=(f'<div class="card"><div class="card-header"><div class="card-title">🟢 Tunnel Active</div>'
                 f'<span class="badge bg"><span class="sdot"></span> LIVE</span></div>'
                 f'<div style="background:var(--surface2);border:1px solid var(--border2);border-radius:var(--radius-sm);'
                 f'padding:1rem;font-family:var(--mono);color:var(--accent);word-break:break-all;margin-bottom:1rem">{pu}</div>'
                 f'<div style="display:flex;gap:.75rem;flex-wrap:wrap">'
                 f'<button class="btn btn-p" onclick="copyText(\'{pu}\',this)">📋 Copy</button>'
                 f'<a href="{pu}" target="_blank" class="btn btn-o">↗ Open</a>'
                 f'<a href="/admin/tunnel/stop" class="btn btn-d" data-confirm="Stop tunnel?">⏹ Stop</a>'
                 f'</div></div>')
        else:
            sec=(f'<div class="card"><div class="card-header"><div class="card-title">Start Quick Tunnel</div>'
                 f'<span class="badge bm">Inactive</span></div>'
                 f'<p style="color:var(--muted);font-size:.875rem;margin-bottom:1.25rem;line-height:1.7">'
                 f'Cloudflare Quick Tunnel — free, HTTPS, no account required. Proxies port {port}.</p>'
                 f'<a href="/admin/tunnel/start" class="btn btn-p btn-lg">🚇 Start Tunnel</a></div>')
        body=f'<div class="page-header"><div><div class="page-title">🚇 Public Tunnel</div></div></div>{sec}'
        return page("Tunnel",body,"tunnel")

    @app.route("/admin/tunnel/start")
    def admin_tunnel_start():
        g=gate()
        if g:return g
        if runtime_ref and not tun_active():
            # Non-blocking: spawn tunnel in background, let browser poll /admin/api/status
            t=threading.Thread(target=runtime_ref.start_tunnel,daemon=True,name="TunnelStart")
            t.start()
        # Redirect immediately; tunnel page polls JS for URL
        return redirect("/admin/tunnel")

    @app.route("/admin/tunnel/stop")
    def admin_tunnel_stop():
        g=gate()
        if g:return g
        if runtime_ref:runtime_ref.stop_tunnel()
        return redirect("/admin/tunnel")

    # Preview / download / delete
    @app.route("/admin/preview/<path:relpath>")
    def admin_preview(relpath):
        g=gate()
        if g:return g
        t=(site_dir/relpath).resolve()
        if not prevent_path_traversal(site_dir,t) or not t.exists():abort(404)
        return sf(str(t),mimetype=mimetypes.guess_type(str(t))[0] or "application/octet-stream")

    @app.route("/admin/dl/<path:relpath>")
    def admin_dl(relpath):
        g=gate()
        if g:return g
        t=(site_dir/relpath).resolve()
        if not prevent_path_traversal(site_dir,t) or not t.exists():abort(404)
        return sf(str(t),as_attachment=True)

    @app.route("/admin/delete/<path:relpath>")
    def admin_delete(relpath):
        g=gate()
        if g:return g
        t=(site_dir/relpath).resolve()
        if prevent_path_traversal(site_dir,t) and t.exists():
            if t.is_dir():shutil.rmtree(str(t))
            else:t.unlink()
        if config.get("hosted_entry")==relpath:
            config["hosted_entry"]=None;save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    # Logs
    @app.route("/admin/logs")
    def admin_logs():
        g=gate()
        if g:return g
        lines=read_logs()
        rows="".join(
            f'<div style="padding:.3rem 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:.75rem;'
            f'color:{"var(--danger)" if "ERROR" in l else "var(--warn)" if "WARNING" in l or " 404 " in l else "var(--success)" if " 200 " in l else "var(--muted)"}">'
            f'{l.replace("<","&lt;")}</div>' for l in lines[-120:]
        )
        body=(f'<div class="page-header"><div class="page-title">📋 Logs</div>'
              f'<a href="/admin/logs/clear" class="btn btn-d btn-sm" data-confirm="Clear logs?">🗑 Clear</a></div>'
              f'<div class="card"><div style="max-height:600px;overflow-y:auto">'
              f'{rows or "<div class=empty-state><span class=empty-icon>📋</span><p>No logs.</p></div>"}'
              f'</div></div>')
        return page("Logs",body,"logs")

    @app.route("/admin/logs/clear")
    def admin_logs_clear():
        g=gate()
        if g:return g
        lf=project_dir/"logs"/"server.log"
        if lf.exists():lf.write_text("")
        return redirect("/admin/logs")

    @app.route("/admin/api/status")
    def admin_api_status():
        g=gate()
        if g:return jsonify({"error":"unauthorized"}),401
        tree=get_tree()
        return jsonify({"hosted_entry":config.get("hosted_entry"),"tunnel_active":tun_active(),
                        "public_url":pub_url(),"file_count":len([f for f in tree if not f["is_dir"]])})


    @app.route("/api/csrf")
    def api_csrf():
        """Return a CSRF token for the current session (used by login form JS)."""
        tok = _csrf_token(app.secret_key)
        from flask import jsonify as _j
        return _j({"token": tok})
    @app.errorhandler(404)
    def nf(e):return "404 Not Found",404
    @app.errorhandler(413)
    def tl(e):return _render_upload("File too large (max 256 MB).","err"),413
    return app

# ── SECTION 11: STORAGE SERVER ────────────────────────────────────────────────
_STORAGE_ALLOWED={
    "txt","pdf","png","jpg","jpeg","gif","webp","svg","mp4","mp3","wav","ogg",
    "zip","tar","gz","csv","json","md","xml","docx","xlsx","pptx","py","js",
    "html","htm","css","eot","woff","woff2","ttf","ico","webm",
}

def build_storage_server(config:Dict[str,Any],runtime_ref=None):
    from flask import Flask,request,redirect,session,send_file as sf,abort

    project_dir=Path(config["project_dir"])
    files_dir=project_dir/"files";files_dir.mkdir(exist_ok=True)
    use_auth=config.get("storage_auth",True)
    pw_hash=config.get("admin_password_hash",_hash_password("admin"))

    app=Flask(__name__)
    app.secret_key=config.get("secret_key",secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"]=True
    app.config["SESSION_COOKIE_SAMESITE"]="Lax"
    app.config["MAX_CONTENT_LENGTH"]=256*1024*1024
    _setup_logging(app,project_dir)

    def authed():return session.get("authenticated",False)
    def gate():
        if use_auth and not authed():return redirect("/login")
        return None

    def get_tree():
        result=[]
        for p in sorted(files_dir.rglob("*")):
            # Only filter hidden parts relative to files_dir, not absolute path ancestors
            rel_parts=p.relative_to(files_dir).parts
            if any(part.startswith(".") or part.startswith("__") for part in rel_parts):continue
            stat=p.stat()
            result.append({"relpath":str(p.relative_to(files_dir)).replace("\\","/"),
                           "name":p.name,"is_dir":p.is_dir(),
                           "size":stat.st_size if p.is_file() else 0,
                           "modified":datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")})
        return result

    def _render(flash_msg=None,flash_type=None):
        tree=get_tree();flist=[f for f in tree if not f["is_dir"]]
        dirs=len(set(str(Path(f["relpath"]).parent) for f in flist if "/" in f["relpath"]))
        total=sum(f["size"] for f in flist)
        widget=_upload_widget("/upload","All common file types · ZIP · Folder upload",_csrf_token(app.secret_key))
        stats=(f'<div class="stats-row">'
               f'<div class="stat-card"><div class="stat-value">{len(flist)}</div><div class="stat-label">Files</div></div>'
               f'<div class="stat-card"><div class="stat-value">{dirs}</div><div class="stat-label">Folders</div></div>'
               f'<div class="stat-card"><div class="stat-value">{format_size(total)}</div><div class="stat-label">Total</div></div>'
               f'</div>')
        if not flist:
            table='<div class="empty-state"><span class="empty-icon">🗄</span><p>No files yet.</p></div>'
        else:
            rows=""
            for f in flist:
                fn=f["relpath"];fname_=f["name"];icon=get_file_icon(fname_)
                folder=str(Path(fn).parent) if "/" in fn else ""
                fhint=f'<div class="fpath">📁 {folder}</div>' if folder else ""
                del_confirm=f'data-confirm="Delete {fname_}?"'
                rows+=(f'<tr><td><div class="fname"><span>{icon}</span>'
                       f'<div><div class="truncate">{_html.escape(fname_)}</div>{fhint}</div></div></td>'
                       f'<td class="fmeta">{format_size(f["size"])}</td>'
                       f'<td class="fmeta">{f["modified"]}</td>'
                       f'<td><div class="actions">'
                       f'<a href="/dl/{fn}" class="btn btn-o btn-sm">⬇ Download</a>'
                       f'<a href="/delete/{fn}" class="btn btn-d btn-sm" {del_confirm}>🗑</a>'
                       f'</div></td></tr>')
            table=(f'<table class="ft"><thead><tr><th>File</th><th>Size</th><th>Modified</th><th>Actions</th></tr></thead>'
                   f'<tbody>{rows}</tbody></table>')
        name=config.get("name","serta")
        body=(f'<div class="page-header"><div><div class="page-title">🗄 File Storage</div>'
              f'<div class="page-sub">Project: {_html.escape(str(name))}</div></div>'
              f'<a href="/logout" class="btn btn-o btn-sm">Logout</a></div>'
              f'{_alert(flash_msg,flash_type)}{stats}'
              f'<div class="card"><div class="card-header"><div class="card-title">Upload</div></div>{widget}</div>'
              f'<div class="card"><div class="card-header"><div class="card-title">Files ({len(flist)})</div></div>{table}</div>')
        return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>File Storage — Serta</title>{_CSS}</head>'
                f'<body style="padding:2rem 1rem;background:var(--bg)">{body}{_JS}</body></html>')

    @app.route("/")
    def index():
        g=gate()
        if g:return g
        return _render()

    @app.route("/login",methods=["GET","POST"])
    def login():
        if not use_auth:session["authenticated"]=True;return redirect("/")
        if request.method=="POST":
            ip=request.remote_addr or "unknown"
            if not _rate_limit_check(ip):
                return _login_page("Too many attempts. Wait 5 minutes."),429
            if not _csrf_validate(app.secret_key):
                return _login_page("Request validation failed. Please refresh."),403
            if check_password(request.form.get("password",""),pw_hash):
                session["authenticated"]=True;return redirect("/")
            _rate_limit_record(ip)
            return _login_page("Incorrect password.","/login"),401
        _csrf_token(app.secret_key)
        return _login_page("","/login")

    @app.route("/logout")
    def logout():session.clear();return redirect("/login")

    @app.route("/upload",methods=["POST"])
    def upload():
        g=gate()
        if g:return g
        if not _csrf_validate(app.secret_key):
            return _render("Request validation failed. Refresh and try again.","err"),403
        flist=request.files.getlist("files")
        mode=request.form.get("upload_mode","")
        saved,errors=process_upload(flist,files_dir,_STORAGE_ALLOWED,mode)
        if saved and not errors:return _render(f"Uploaded {len(saved)} file(s).","ok")
        if saved:return _render(f"Uploaded {len(saved)} | Errors: {'; '.join(errors[:3])}","warn")
        return _render("Failed: "+"; ".join(errors[:5]),"err")

    @app.route("/dl/<path:relpath>")
    def dl(relpath):
        g=gate()
        if g:return g
        t=(files_dir/relpath).resolve()
        if not prevent_path_traversal(files_dir,t) or not t.exists():abort(404)
        return sf(str(t),as_attachment=True)

    @app.route("/delete/<path:relpath>")
    def delete_file(relpath):
        g=gate()
        if g:return g
        t=(files_dir/relpath).resolve()
        if prevent_path_traversal(files_dir,t) and t.exists():
            if t.is_dir():shutil.rmtree(str(t))
            else:t.unlink()
        return _render(f"Deleted: {Path(relpath).name}","ok")

    @app.route("/api/csrf")
    def api_csrf_st():
        from flask import jsonify as _j
        return _j({"token":_csrf_token(app.secret_key)})

    @app.errorhandler(404)
    def nf(e):return "404 Not Found",404
    @app.errorhandler(413)
    def tl(e):return _render("File too large (max 256 MB).","err"),413
    return app

# ── SECTION 12: APP SERVER ────────────────────────────────────────────────────
def build_app_server(config:Dict[str,Any],runtime_ref=None):
    from flask import Flask,request,jsonify
    project_dir=Path(config["project_dir"])
    db_path=config.get("db_path",str(project_dir/"data"/"app.db"))
    Path(db_path).parent.mkdir(parents=True,exist_ok=True)
    app=Flask(__name__);app.secret_key=config.get("secret_key",secrets.token_hex(32))
    _setup_logging(app,project_dir)

    from contextlib import contextmanager as _cm
    @_cm
    def get_db():
        """Context manager: opens, yields, commits on success, closes always."""
        c=sqlite3.connect(db_path,timeout=10);c.row_factory=sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def init_db():
        with get_db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,value TEXT,created TEXT DEFAULT(datetime('now')))""")
            db.execute("""CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,detail TEXT,ts TEXT DEFAULT(datetime('now')))""")
            db.commit()
    init_db()

    def log_a(action,detail=""):
        with get_db() as db:db.execute("INSERT INTO logs(action,detail) VALUES(?,?)",(action,detail));db.commit()

    name=config.get("name","serta")
    @app.route("/")
    def index():
        return (f'<!DOCTYPE html><html><head><meta charset=UTF-8><title>{name}</title>'
                f'<style>body{{background:#080c10;color:#cdd9e5;font-family:sans-serif;padding:2rem}}'
                f'h1{{color:#00d4aa}}table{{border-collapse:collapse;width:100%;margin-top:1rem}}'
                f'th,td{{padding:.5rem 1rem;text-align:left;border-bottom:1px solid #1e2d3d}}'
                f'th{{background:#0d1219;color:#546e7a}}</style></head>'
                f'<body><h1>⚡ {name}</h1><p style="color:#546e7a;margin-bottom:1rem">REST API + SQLite</p>'
                f'<table><thead><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr></thead>'
                f'<tbody><tr><td>GET</td><td>/api/health</td><td>Health check</td></tr>'
                f'<tr><td>GET</td><td>/api/items</td><td>List items</td></tr>'
                f'<tr><td>POST</td><td>/api/items</td><td>Create item</td></tr>'
                f'<tr><td>GET/PUT/DELETE</td><td>/api/items/&lt;id&gt;</td><td>CRUD</td></tr>'
                f'</tbody></table></body></html>'),200

    @app.route("/api/health")
    def health():
        try:
            with get_db() as db:c=db.execute("SELECT COUNT(*) FROM items").fetchone()[0];s="ok"
        except Exception as e:c=0;s=str(e)
        return jsonify({"status":"ok","db":s,"items":c,"ts":datetime.datetime.utcnow().isoformat()+"Z"})

    @app.route("/api/items",methods=["GET"])
    def list_items():
        with get_db() as db:rows=db.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/items",methods=["POST"])
    def create_item():
        d=request.get_json(silent=True) or {}
        n=str(d.get("name","")).strip();v=str(d.get("value","")).strip()
        if not n:return jsonify({"error":"name required"}),400
        with get_db() as db:
            cur=db.execute("INSERT INTO items(name,value) VALUES(?,?)",(n,v));db.commit();iid=cur.lastrowid
        log_a("CREATE",f"id={iid}")
        with get_db() as db:row=db.execute("SELECT * FROM items WHERE id=?",(iid,)).fetchone()
        return jsonify(dict(row)),201

    @app.route("/api/items/<int:iid>",methods=["GET"])
    def get_item(iid):
        with get_db() as db:row=db.execute("SELECT * FROM items WHERE id=?",(iid,)).fetchone()
        return (jsonify(dict(row)) if row else (jsonify({"error":"not found"}),404))

    @app.route("/api/items/<int:iid>",methods=["PUT"])
    def update_item(iid):
        d=request.get_json(silent=True) or {}
        n=str(d.get("name","")).strip();v=str(d.get("value","")).strip()
        with get_db() as db:
            if not db.execute("SELECT id FROM items WHERE id=?",(iid,)).fetchone():
                return jsonify({"error":"not found"}),404
            db.execute("UPDATE items SET name=?,value=? WHERE id=?",(n,v,iid));db.commit()
        log_a("UPDATE",f"id={iid}")
        with get_db() as db:row=db.execute("SELECT * FROM items WHERE id=?",(iid,)).fetchone()
        return jsonify(dict(row))

    @app.route("/api/items/<int:iid>",methods=["DELETE"])
    def delete_item(iid):
        with get_db() as db:
            if not db.execute("SELECT id FROM items WHERE id=?",(iid,)).fetchone():
                return jsonify({"error":"not found"}),404
            db.execute("DELETE FROM items WHERE id=?",(iid,));db.commit()
        log_a("DELETE",f"id={iid}")
        return jsonify({"deleted":iid})

    @app.route("/api/logs")
    def get_logs():
        with get_db() as db:rows=db.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 100").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.errorhandler(404)
    def nf(e):return jsonify({"error":"not found"}),404
    @app.errorhandler(500)
    def se(e):return jsonify({"error":"server error"}),500
    return app

# ── SECTION 13: BOT PROCESS ───────────────────────────────────────────────────
class BotProcess:
    def __init__(self,entry:Path,env_vars:Dict[str,str]):
        self.entry=entry;self.env=env_vars;self.proc=None
        self.log_buf:List[str]=[];self._lock=threading.Lock();self.pid=None

    def start(self):
        if self.proc and self.proc.poll() is None:return
        env={**os.environ,**self.env}
        self.proc=subprocess.Popen(
            [sys.executable,"-u",str(self.entry)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            text=True,env=env,cwd=str(self.entry.parent))
        self.pid=self.proc.pid
        with self._lock:
            self.log_buf=[f"[Serta] Bot started (PID {self.pid}) — {datetime.datetime.now().strftime('%H:%M:%S')}"]
        threading.Thread(target=self._read,daemon=True).start()

    def _read(self):
        # Capture stdout reference before loop so stop() setting proc=None is safe
        stdout = self.proc.stdout
        if stdout is None: return
        try:
            for line in stdout:
                with self._lock:
                    self.log_buf.append(line.rstrip())
                    if len(self.log_buf)>500:self.log_buf=self.log_buf[-400:]
        except (ValueError, OSError):
            pass  # Pipe closed (process killed)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:self.proc.kill()
        self.proc=None;self.pid=None
        with self._lock:
            self.log_buf.append(f"[Serta] Bot stopped — {datetime.datetime.now().strftime('%H:%M:%S')}")

    def restart(self):self.stop();time.sleep(0.5);self.start()

    @property
    def running(self):return self.proc is not None and self.proc.poll() is None

    def get_logs(self):
        with self._lock:return "\n".join(self.log_buf[-200:])

# ── SECTION 14: BOT SERVER ────────────────────────────────────────────────────
_BOT_ALLOWED={"py","txt","json","yaml","yml","toml","env","md","cfg","ini",
              "png","jpg","jpeg","gif","svg","mp3","wav","csv","xml","zip"}

def build_bot_server(config:Dict[str,Any],runtime_ref=None):
    from flask import Flask,request,redirect,session,jsonify,send_file as sf

    project_dir=Path(config["project_dir"])
    bot_dir=Path(config.get("bot_dir",str(project_dir/"bot")))
    bot_dir.mkdir(parents=True,exist_ok=True)
    (project_dir/"bot_logs").mkdir(exist_ok=True)
    pw_hash=config.get("admin_password_hash",_hash_password("admin"))
    bot_type=config.get("bot_type","generic")

    _state:Dict[str,Any]={"proc":None}  # mutable closure
    _state_lock=threading.Lock()  # protects concurrent bot start/stop

    app=Flask(__name__)
    app.secret_key=config.get("secret_key",secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"]=True
    app.config["SESSION_COOKIE_SAMESITE"]="Lax"
    app.config["MAX_CONTENT_LENGTH"]=256*1024*1024
    _setup_logging(app,project_dir)

    def is_admin():return session.get("admin_authed",False)
    def gate():
        if not is_admin():return redirect("/admin/login")
        return None
    def bp()->Optional[BotProcess]:
        with _state_lock:return _state.get("proc")

    def get_bot_files():
        result=[]
        for p in sorted(bot_dir.rglob("*")):
            # Only filter on the relative path parts — not the absolute path,
            # which may contain hidden dirs like .local/.config in the system prefix
            rel_parts=p.relative_to(bot_dir).parts
            if any(part.startswith(".") or part.startswith("__") for part in rel_parts):continue
            stat=p.stat()
            result.append({"relpath":str(p.relative_to(bot_dir)).replace("\\","/"),
                           "name":p.name,"is_dir":p.is_dir(),
                           "size":stat.st_size if p.is_file() else 0,
                           "modified":datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")})
        return result

    def _install_deps(deps):
        if not deps:return True
        r=subprocess.run([sys.executable,"-m","pip","install","--quiet"]+list(deps),capture_output=True,text=True)
        return r.returncode==0

    def _nav(active):
        def _n(href,ic,lb,k):
            cls="nav-item active" if active==k else "nav-item"
            return f'<a href="{href}" class="{cls}"><span style="width:16px;text-align:center;flex-shrink:0">{ic}</span>{lb}</a>'
        return (_n("/admin","🤖","Bot Dashboard","dash")+
                _n("/admin/upload","📤","Upload Files","upload")+
                _n("/admin/env","🔑","Tokens & Env","env")+
                _n("/admin/deps","📦","Dependencies","deps")+
                _n("/admin/logs","📋","Logs","logs"))

    def page(title,body,active,flash_msg=None,flash_type=None):
        return _shell(title,_alert(flash_msg,flash_type)+body,active,
                      config.get("name","bot"),_nav(active))

    # Login
    @app.route("/admin/login",methods=["GET","POST"])
    def admin_login():
        if request.method=="POST":
            ip=request.remote_addr or "unknown"
            if not _rate_limit_check(ip):
                return _login_page("Too many attempts. Wait 5 minutes."),429
            if not _csrf_validate(app.secret_key):
                return _login_page("Request validation failed. Try again."),403
            if check_password(request.form.get("password",""),pw_hash):
                session["admin_authed"]=True;return redirect("/admin")
            _rate_limit_record(ip)
            return _login_page("Incorrect password."),401
        _csrf_token(app.secret_key)
        return _login_page()

    @app.route("/admin/logout")
    def admin_logout():session.clear();return redirect("/admin/login")

    # Dashboard
    @app.route("/admin")
    @app.route("/admin/")
    def admin_dash():
        g=gate()
        if g:return g
        proc=bp();running=proc.running if proc else False
        entry=config.get("bot_entry")
        sbadge=('<span class="badge bg"><span class="sdot"></span> Running</span>' if running
                else '<span class="badge br"><span class="sdot"></span> Stopped</span>')
        pid_info=f"PID {proc.pid}" if (running and proc) else "Stopped"
        bot_files=[f for f in get_bot_files() if not f["is_dir"]]
        py_files=[f for f in bot_files if f["name"].endswith(".py")]
        opts="".join(f'<option value="{f["relpath"]}" {"selected" if entry==f["relpath"] else ""}>{f["relpath"]}</option>' for f in py_files)
        entry_block=(
            f'<form method="POST" action="/admin/set-entry" style="display:flex;gap:.5rem;flex-wrap:wrap">'
            f'<input type="hidden" name="_csrf_token" value="{_csrf_token(app.secret_key)}">'
            f'<select name="entry" style="flex:1;margin:0">{opts}</select>'
            f'<button class="btn btn-p" type="submit">Set Entry Point</button></form>'
            if opts else '<div class="alert aw">⚠ Upload a .py bot script first.</div>'
        )
        controls=(
            '<div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem">'
            +('<a href="/admin/bot/stop" class="btn btn-d">⏹ Stop Bot</a>'
               '<a href="/admin/bot/restart" class="btn btn-w">🔄 Restart</a>' if running
               else f'<a href="/admin/bot/start" class="btn btn-g">▶ Start Bot</a>')
            +'</div>'
        )
        terminal=(f'<div id="bot-terminal" class="bot-terminal">'
                  f'{proc.get_logs() if proc else "[No output yet — start the bot to see logs]"}'
                  f'</div>')
        body=(f'<div class="page-header">'
              f'<div><div class="page-title">🤖 Bot Dashboard</div>'
              f'<div class="page-sub">Platform: <strong>{bot_type.title()}</strong> · {pid_info}</div></div>'
              f'{sbadge}</div>'
              f'<div class="stats-row">'
              f'<div class="stat-card"><div class="stat-value">{"🟢" if running else "🔴"}</div><div class="stat-label">Status</div></div>'
              f'<div class="stat-card"><div class="stat-value">{len(bot_files)}</div><div class="stat-label">Files</div></div>'
              f'<div class="stat-card"><div class="stat-value">{len(config.get("bot_pip_deps",[]))}</div><div class="stat-label">Packages</div></div>'
              f'</div>'
              f'<div class="card"><div class="card-title" style="margin-bottom:.75rem">Entry Script</div>'
              f'{entry_block}{controls}</div>'
              f'<div class="card"><div class="card-header"><div class="card-title">Live Output</div>'
              f'<span style="font-size:.75rem;color:var(--muted)">Auto-refreshes every 3s</span></div>'
              f'{terminal}</div>')
        return page("Bot Dashboard",body,"dash")

    @app.route("/admin/set-entry",methods=["POST"])
    def set_entry():
        g=gate()
        if g:return g
        if not _csrf_validate(app.secret_key):
            return redirect("/admin")
        entry=request.form.get("entry","").strip()
        t=(bot_dir/entry).resolve()
        if prevent_path_traversal(bot_dir,t) and t.exists() and t.name.endswith(".py"):
            config["bot_entry"]=entry;save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    # Bot controls
    @app.route("/admin/bot/start")
    def bot_start():
        g=gate()
        if g:return g
        entry=config.get("bot_entry")
        if not entry:return redirect("/admin")
        t=(bot_dir/entry).resolve()
        if not prevent_path_traversal(bot_dir,t) or not t.exists():return redirect("/admin")
        deps=config.get("bot_pip_deps",[])
        if deps:_install_deps(deps)
        proc=BotProcess(t,{**config.get("bot_env",{})})
        proc.start()
        with _state_lock:_state["proc"]=proc
        config["bot_status"]="running";save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    @app.route("/admin/bot/stop")
    def bot_stop():
        g=gate()
        if g:return g
        with _state_lock:
            p=_state.get("proc")
            if p:p.stop();_state["proc"]=None
        config["bot_status"]="stopped";save_config(Path(config["project_dir"]),config)
        return redirect("/admin")

    @app.route("/admin/bot/restart")
    def bot_restart():
        g=gate()
        if g:return g
        with _state_lock:
            p=_state.get("proc")
            if p:p.restart()
        return redirect("/admin")

    @app.route("/admin/bot/logs-raw")
    def bot_logs_raw():
        if not is_admin():
            from flask import jsonify as _jj
            return _jj({"error":"unauthorized"}),401
        logs=bp().get_logs() if bp() else "[No bot process running. Start bot first.]"
        return logs,200,{"Content-Type":"text/plain;charset=utf-8"}

    # Upload
    @app.route("/admin/upload",methods=["GET","POST"])
    def admin_upload():
        g=gate()
        if g:return g
        if request.method=="POST":
            if not _csrf_validate(app.secret_key):
                return _render_upload("Request validation failed. Refresh and try again.","err"),403
            flist=request.files.getlist("files")
            mode=request.form.get("upload_mode","")
            saved,errors=process_upload(flist,bot_dir,_BOT_ALLOWED,mode)
            if saved and not errors:return _render_upload(f"Uploaded {len(saved)}.","ok")
            if saved:return _render_upload(f"Uploaded {len(saved)} | {'; '.join(errors[:3])}","warn")
            return _render_upload("Failed: "+"; ".join(errors[:5]),"err")
        return _render_upload()

    def _render_upload(flash_msg=None,flash_type=None):
        widget=_upload_widget("/admin/upload",".py · .json · .yaml · .env · .txt · ZIP · Folder",_csrf_token(app.secret_key))
        files=[f for f in get_bot_files() if not f["is_dir"]]
        row_parts=[]
        for f in files:
            icon="🐍" if f["name"].endswith(".py") else "📄"
            dc=f'data-confirm="Delete {f["name"]}?"'
            row_parts.append(
                f'<tr><td><div class="fname"><span>{icon}</span>'
                f'<span>{f["relpath"]}</span></div></td>'
                f'<td class="fmeta">{format_size(f["size"])}</td>'
                f'<td class="fmeta">{f["modified"]}</td>'
                f'<td><a href="/admin/delete/{f["relpath"]}" class="btn btn-d btn-sm" {dc}>🗑</a></td></tr>'
            )
        rows="".join(row_parts)
        table=(f'<table class="ft"><thead><tr><th>File</th><th>Size</th><th>Modified</th><th></th></tr></thead>'
               f'<tbody>{rows}</tbody></table>' if files
               else '<div class="empty-state"><span class="empty-icon">📂</span><p>No files uploaded.</p></div>')
        body=(f'<div class="page-header"><div><div class="page-title">📤 Upload Bot Files</div>'
              f'<div class="page-sub">Upload Python scripts, config files, assets, or a full folder</div></div></div>'
              f'<div class="card">{widget}</div>'
              f'<div class="card"><div class="card-title" style="margin-bottom:.75rem">Bot Files ({len(files)})</div>{table}</div>')
        return page("Upload",body,"upload",flash_msg,flash_type)

    @app.route("/admin/delete/<path:relpath>")
    def admin_delete(relpath):
        g=gate()
        if g:return g
        t=(bot_dir/relpath).resolve()
        if prevent_path_traversal(bot_dir,t) and t.exists():
            t.unlink() if t.is_file() else shutil.rmtree(str(t))
        if config.get("bot_entry")==relpath:
            config["bot_entry"]=None;save_config(Path(config["project_dir"]),config)
        return redirect("/admin/upload")

    # Env vars
    @app.route("/admin/env",methods=["GET","POST"])
    def admin_env():
        g=gate()
        if g:return g
        if request.method=="POST":
            if not _csrf_validate(app.secret_key):
                return redirect("/admin/env?err=csrf")
            keys=request.form.getlist("env_key[]");vals=request.form.getlist("env_val[]")
            config["bot_env"]={k.strip():v.strip() for k,v in zip(keys,vals) if k.strip()}
            save_config(Path(config["project_dir"]),config)
            return redirect("/admin/env?saved=1")
        saved_msg=_alert("Variables saved.","ok") if request.args.get("saved") else ""
        env=config.get("bot_env",{})
        rows="".join(
            f'<div class="env-row">'
            f'<input type="text" name="env_key[]" value="{_html.escape(k)}" placeholder="KEY" style="margin:0">'
            f'<input type="text" name="env_val[]" value="{_html.escape(v)}" placeholder="value" style="margin:0">'
            f'<button type="button" class="btn btn-d btn-sm" onclick="this.closest(\'.env-row\').remove()">✕</button>'
            f'</div>' for k,v in env.items()
        )
        # Platform-specific token hints
        hints={"discord":"DISCORD_TOKEN — your bot token from discord.com/developers",
               "telegram":"TELEGRAM_TOKEN — from @BotFather on Telegram",
               "slack":"SLACK_BOT_TOKEN + SLACK_SIGNING_SECRET"}
        hint_html=""
        if bot_type in hints:
            hint_html=f'<div class="alert ai">ℹ {hints[bot_type]}</div>'
        body=(f'<div class="page-header"><div class="page-title">🔑 Tokens &amp; Env Vars</div></div>'
              f'{saved_msg}{hint_html}'
              f'<div class="card"><p style="color:var(--muted);font-size:.875rem;margin-bottom:1rem;line-height:1.7">'
              f'Injected as environment variables when the bot starts. Store tokens, API keys, secrets here.</p>'
              f'<form method="POST"><input type="hidden" name="_csrf_token" value="{_csrf_token(app.secret_key)}"><div id="env-container">{rows}</div>'
              f'<button type="button" class="btn btn-o btn-sm" onclick="addEnvRow()" style="margin:.5rem 0">+ Add Variable</button>'
              f'<div style="margin-top:1rem;display:flex;gap:.75rem">'
              f'<button type="submit" class="btn btn-p">Save Variables</button></div></form></div>')
        return page("Tokens & Env",body,"env")

    # Dependencies
    @app.route("/admin/deps",methods=["GET","POST"])
    def admin_deps():
        g=gate()
        if g:return g
        install_result=""
        if request.method=="POST":
            if not _csrf_validate(app.secret_key):
                return redirect("/admin/deps?err=csrf")
            new_pkg=request.form.get("new_pkg","").strip()
            deps=config.get("bot_pip_deps",[])[:]
            if new_pkg and new_pkg not in deps:
                deps.append(new_pkg);config["bot_pip_deps"]=deps
                save_config(Path(config["project_dir"]),config)
            if request.form.get("action")=="install_all":
                ok_i=_install_deps(config.get("bot_pip_deps",[]))
                install_result=_alert("All packages installed successfully.","ok") if ok_i else _alert("Some packages failed — check terminal logs.","err")
        deps=config.get("bot_pip_deps",[])
        # Default packages hint
        platform_defaults={"discord":["discord.py"],"telegram":["python-telegram-bot"],
                           "slack":["slack-bolt"],"generic":[]}
        defaults=platform_defaults.get(bot_type,[])
        missing=[d for d in defaults if d not in deps]
        missing_html=(f'<div class="alert aw">⚠ Suggested for {bot_type}: '
                      +", ".join(f'<strong>{m}</strong>' for m in missing)
                      +f' — <a href="/admin/deps/add-defaults" style="color:var(--accent)">Add all →</a></div>'
                      if missing else "")
        rows="".join(
            f'<tr><td class="mono">{d}</td>'
            f'<td><a href="/admin/deps/remove/{d}" class="btn btn-d btn-sm" data-confirm="Remove {d}?">Remove</a></td></tr>'
            for d in deps
        )
        table=(f'<table class="ft"><thead><tr><th>Package</th><th></th></tr></thead><tbody>{rows}</tbody></table>'
               if deps else '<p style="color:var(--muted)">No packages added yet.</p>')
        body=(f'<div class="page-header"><div class="page-title">📦 Dependencies</div></div>'
              f'{install_result}{missing_html}'
              f'<div class="card"><form method="POST">'
              f'<input type="hidden" name="_csrf_token" value="{_csrf_token(app.secret_key)}">'
              f'<div style="display:flex;gap:.75rem;margin-bottom:1rem">'
              f'<input type="text" name="new_pkg" placeholder="package-name e.g. requests" style="margin:0;flex:1">'
              f'<button type="submit" class="btn btn-p">Add</button></div></form>'
              f'{table}</div>'
              +(f'<div class="card"><form method="POST">'
                f'<input type="hidden" name="_csrf_token" value="{_csrf_token(app.secret_key)}">'
                f'<input type="hidden" name="action" value="install_all">'
                f'<button type="submit" class="btn btn-g">⬇ Install All Packages Now</button></form></div>'
                if deps else ""))
        return page("Dependencies",body,"deps")

    @app.route("/admin/deps/remove/<pkg>")
    def remove_dep(pkg):
        g=gate()
        if g:return g
        deps=config.get("bot_pip_deps",[])[:]
        if pkg in deps:deps.remove(pkg)
        config["bot_pip_deps"]=deps;save_config(Path(config["project_dir"]),config)
        return redirect("/admin/deps")

    @app.route("/admin/deps/add-defaults")
    def add_defaults():
        g=gate()
        if g:return g
        defaults={"discord":["discord.py"],"telegram":["python-telegram-bot"],"slack":["slack-bolt"]}
        for d in defaults.get(bot_type,[]):
            if d not in config.get("bot_pip_deps",[]):
                config.setdefault("bot_pip_deps",[]).append(d)
        save_config(Path(config["project_dir"]),config)
        return redirect("/admin/deps")

    # Logs
    @app.route("/admin/logs")
    def admin_logs():
        g=gate()
        if g:return g
        lf=project_dir/"logs"/"server.log"
        lines=lf.read_text(errors="replace").splitlines() if lf.exists() else []
        rows="".join(
            f'<div style="padding:.3rem 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:.75rem;'
            f'color:{"var(--danger)" if "ERROR" in l else "var(--muted)"}">{l.replace("<","&lt;")}</div>'
            for l in lines[-150:]
        )
        body=(f'<div class="page-header"><div class="page-title">📋 Server Logs</div></div>'
              f'<div class="card"><div style="max-height:600px;overflow-y:auto">'
              f'{rows or "<div class=empty-state><span class=empty-icon>📋</span><p>No logs.</p></div>"}'
              f'</div></div>')
        return page("Logs",body,"logs")

    @app.route("/api/csrf")
    def api_csrf_bot():
        from flask import jsonify as _j
        return _j({"token":_csrf_token(app.secret_key)})

    @app.route("/")
    def index_redirect():return redirect("/admin")
    @app.errorhandler(404)
    def nf(e):return "404 Not Found",404
    @app.errorhandler(413)
    def tl(e):return "File too large (max 256 MB)",413
    return app

# ── SECTION 15: LOGGING ───────────────────────────────────────────────────────
def _setup_logging(app,project_dir:Path):
    ld=project_dir/"logs";ld.mkdir(exist_ok=True)
    log_path=str(ld/"server.log")
    # Prevent duplicate handlers on server restart
    if not any(isinstance(h,logging.FileHandler) and h.baseFilename==log_path
               for h in app.logger.handlers):
        h=logging.FileHandler(log_path);h.setLevel(logging.INFO)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s","%Y-%m-%d %H:%M:%S"))
        app.logger.addHandler(h);app.logger.setLevel(logging.INFO)
    wz=logging.getLogger("werkzeug")
    if not any(isinstance(h,logging.FileHandler) and h.baseFilename==log_path
               for h in wz.handlers):
        h2=logging.FileHandler(log_path);h2.setLevel(logging.INFO)
        h2.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s","%Y-%m-%d %H:%M:%S"))
        wz.addHandler(h2);wz.setLevel(logging.INFO)

# ── SECTION 16: SERVER RUNTIME ────────────────────────────────────────────────
class ServerRuntime:
    def __init__(self,config:Dict[str,Any]):
        self.config=config;self.app=None;self.thread=None
        self.running=False;self.port=config.get("port",5000)
        self.tunnel_proc=None;self.public_url=None

    def _build_app(self):
        t=self.config.get("server_type","web")
        if t=="web":return build_web_server(self.config,self)
        if t=="app":return build_app_server(self.config,self)
        if t=="storage":return build_storage_server(self.config,self)
        if t=="bot":return build_bot_server(self.config,self)
        raise ValueError(f"Unknown type: {t}")

    def _check_port(self):
        """Return True if port is free, False if already in use."""
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            # Do NOT set SO_REUSEADDR — we want to detect occupied ports
            s.bind(("",self.port))
            s.close()
            return True
        except OSError:
            return False

    def start(self):
        if self.running:warn("Already running.");return
        if not self._check_port():
            err(f"Port {self.port} is already in use. Choose a different port.")
            return
        try:
            self.app=self._build_app()
            self.thread=threading.Thread(target=self._run_flask,daemon=True,name="Flask")
            self.thread.start();time.sleep(1.2);self.running=True
            ok(f"Server started → http://127.0.0.1:{self.port}")
            if self.config.get("server_type") in ("web","bot","storage"):
                ok(f"Admin panel  → http://127.0.0.1:{self.port}/admin")
        except Exception as e:err(f"Start failed: {e}");traceback.print_exc()

    def _run_flask(self):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self.app.run(host="0.0.0.0",port=self.port,threaded=True,use_reloader=False)

    def stop(self):
        if not self.running:return
        self.stop_tunnel()
        # If bot server, also stop the bot process
        if hasattr(self,"_bot_state") and self._bot_state:
            p=self._bot_state.get("proc")
            if p and p.running:p.stop()
        try:
            import urllib.request as _ur;_ur.urlopen(f"http://127.0.0.1:{self.port}/__shutdown__",timeout=2)
        except Exception:pass
        self.running=False;self.app=None;self.thread=None;ok("Server stopped.")

    def restart(self):step("Restarting…");self.stop();time.sleep(0.5);self.start()

    def _find_cf(self):
        for c in [shutil.which("cloudflared"),"/usr/local/bin/cloudflared",
                  str(Path.home()/".local"/"bin"/"cloudflared"),
                  str(Path.home()/"bin"/"cloudflared")]:
            if c and Path(c).is_file():return c
        return None

    def _auto_install_cf(self):
        plat=platform.system().lower();mach=platform.machine().lower()
        section("Auto-Installing cloudflared")
        if plat=="linux":
            arch="arm64" if ("arm" in mach or "aarch64" in mach) else "amd64"
            for cmd in [["sudo","apt-get","install","-y","cloudflared"],
                        ["sudo","dnf","install","-y","cloudflared"],
                        ["snap","install","cloudflared","--classic"]]:
                if subprocess.run(cmd,capture_output=True).returncode==0:
                    f=self._find_cf()
                    if f:ok(f"Installed → {f}");return f
            url=f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}"
            dest=Path.home()/".local"/"bin"/"cloudflared";dest.parent.mkdir(parents=True,exist_ok=True)
            try:urllib.request.urlretrieve(url,str(dest));dest.chmod(0o755);return str(dest)
            except Exception as e:err(f"Download failed: {e}")
        elif plat=="darwin":
            brew=shutil.which("brew")
            if brew and subprocess.run([brew,"install","cloudflared"],capture_output=True).returncode==0:
                f=self._find_cf()
                if f:return f
            arch="amd64" if "x86" in mach else "arm64"
            url=f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}.tgz"
            dest_dir=Path.home()/".local"/"bin";dest_dir.mkdir(parents=True,exist_ok=True)
            try:
                import tarfile;tgz=dest_dir/"cloudflared.tgz"
                urllib.request.urlretrieve(url,str(tgz))
                with tarfile.open(str(tgz)) as tf:tf.extractall(str(dest_dir))
                tgz.unlink(missing_ok=True)
                cf=dest_dir/"cloudflared"
                if cf.exists():cf.chmod(0o755);return str(cf)
            except Exception as e:err(f"Download failed: {e}")
        elif plat=="windows":
            wg=shutil.which("winget")
            if wg and subprocess.run([wg,"install","--id","Cloudflare.cloudflared","-e","--silent"],capture_output=True).returncode==0:
                f=self._find_cf()
                if f:return f
            dest=Path.home()/"AppData"/"Local"/"cloudflared.exe"
            try:
                urllib.request.urlretrieve("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",str(dest))
                return str(dest)
            except Exception as e:err(f"Download failed: {e}")
        err("Auto-install failed. https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        return None

    def start_tunnel(self):
        if self.tunnel_proc:warn("Tunnel already running.");return
        cf=self._find_cf()
        if not cf:warn("cloudflared not found — auto-installing…");cf=self._auto_install_cf()
        if not cf:err("Could not install cloudflared.");return
        ok(f"cloudflared: {cf}");step(f"Starting Quick Tunnel → localhost:{self.port}…")
        try:
            self.tunnel_proc=subprocess.Popen(
                [cf,"tunnel","--url",f"http://localhost:{self.port}"],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            spinner("Waiting for tunnel URL",2.0)
            url=self._parse_tunnel_url(20)
            if url:self.public_url=url;ok(f"Public URL: {C.BGREEN}{C.BOLD}{url}{C.RESET}")
            else:warn("Tunnel started — URL not yet visible.")
        except Exception as e:err(f"Tunnel error: {e}")

    def _parse_tunnel_url(self,timeout=15):
        if not self.tunnel_proc:return None
        deadline=time.time()+timeout
        try:
            while time.time()<deadline:
                proc=self.tunnel_proc
                if proc is None:break  # tunnel stopped
                line=proc.stdout.readline()
                if not line:time.sleep(0.1);continue
                m=re.search(r"https://[a-z0-9\-]+\.(trycloudflare|cfargotunnel)\.com",line)
                if m:return m.group(0)
        except (ValueError,OSError):pass  # pipe closed
        return None

    def stop_tunnel(self):
        if not self.tunnel_proc:return
        proc=self.tunnel_proc;self.tunnel_proc=None;self.public_url=None
        try:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
        except Exception:pass
        ok("Tunnel stopped.")

    def local_url(self):return f"http://127.0.0.1:{self.port}"
    def network_url(self):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(("8.8.8.8",80));ip=s.getsockname()[0];s.close();return f"http://{ip}:{self.port}"
        except Exception:return self.local_url()

# ── SECTION 17: TERMINAL CONTROL PANEL ───────────────────────────────────────
def print_status_panel(rt:ServerRuntime):
    cfg=rt.config;name=cfg.get("name","?");stype=cfg.get("server_type","?").replace("_"," ").title()
    srv=f"{C.BGREEN}● Running{C.RESET}" if rt.running else f"{C.BRED}● Stopped{C.RESET}"
    tun=f"{C.BGREEN}● {rt.public_url}{C.RESET}" if rt.tunnel_proc else f"{C.BRED}● Inactive{C.RESET}"
    section(f"Control Panel — {name}")
    print(f"  {'Type':<22} {stype}")
    print(f"  {'Status':<22} {srv}")
    print(f"  {'Local URL':<22} {C.BCYAN}{rt.local_url()}{C.RESET}")
    if cfg.get("server_type") in ("web","bot","storage"):
        print(f"  {'Admin Panel':<22} {C.BCYAN}{rt.local_url()}/admin{C.RESET}")
    print(f"  {'Network URL':<22} {C.CYAN}{rt.network_url()}{C.RESET}")
    print(f"  {'Public Tunnel':<22} {tun}")
    hr()

def run_control_panel(rt:ServerRuntime):
    while True:
        print_status_panel(rt)
        choice=menu("Server Controls",[
            ("1","Stop Server" if rt.running else "Start Server"),
            ("2","Restart"),("3","Start Public Tunnel"),("4","Stop Tunnel"),
            ("5","View Logs"),("6","Project Info"),("7","Open in Browser"),("0","Back"),
        ])
        if choice=="1":
            if rt.running:rt.stop()
            else:rt.start()
        elif choice=="2":rt.restart()
        elif choice=="3":
            if not rt.running:err("Start the server first.")
            else:rt.start_tunnel()
        elif choice=="4":rt.stop_tunnel()
        elif choice=="5":
            lf=Path(rt.config["project_dir"])/"logs"/"server.log"
            section("Logs")
            if not lf.exists():warn("No logs yet.")
            else:
                lines=lf.read_text(errors="replace").splitlines()
                for l in lines[-50:]:
                    if "ERROR" in l:print(f"  {C.BRED}{l}{C.RESET}")
                    elif "WARNING" in l:print(f"  {C.BYELLOW}{l}{C.RESET}")
                    else:print(f"  {C.DIM}{l}{C.RESET}")
        elif choice=="6":
            section("Project Info")
            for k,v in rt.config.items():
                if k in ("secret_key","admin_password_hash"):v="****"
                if k=="bot_env" and isinstance(v,dict):v={kk:"****" for kk in v}
                print(f"  {C.BCYAN}{k:<28}{C.RESET} {v}")
        elif choice=="7":
            try:import webbrowser;webbrowser.open(rt.local_url());ok("Opened.")
            except Exception:warn(f"Could not open browser. Open manually: {rt.local_url()}")
        elif choice=="0":
            if rt.running and confirm("Stop server before exiting?",True):rt.stop()
            break
        else:warn("Invalid choice.")
        input(f"\n  {C.DIM}Press Enter…{C.RESET}")

# ── SECTION 18: SYSTEM INFO ───────────────────────────────────────────────────
def print_system_info():
    section("System Information")
    print(f"  {'OS':<22} {platform.system()} {platform.release()}")
    print(f"  {'Architecture':<22} {platform.machine()}")
    print(f"  {'Python':<22} {sys.version.split()[0]}")
    print(f"  {'Hostname':<22} {socket.gethostname()}")
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(("8.8.8.8",80));ip=s.getsockname()[0];s.close()
    except Exception:ip="N/A"
    print(f"  {'Local IP':<22} {ip}")
    print(f"  {'Serta Projects':<22} {PROJECTS_DIR}")
    cf=next((c for c in [shutil.which("cloudflared"),"/usr/local/bin/cloudflared",
             str(Path.home()/".local"/"bin"/"cloudflared")] if c and Path(c).is_file()),None)
    print(f"  {'cloudflared':<22} {C.BGREEN+cf+C.RESET if cf else C.BYELLOW+'Not installed (auto-installs on use)'+C.RESET}")

# ── SECTION 19: MAIN ──────────────────────────────────────────────────────────
def main():
    signal.signal(signal.SIGINT,lambda *_:(print(f"\n{C.BYELLOW}Interrupted.{C.RESET}"),sys.exit(0)))
    banner();run_startup_checks();print_system_info()
    runtime:Optional[ServerRuntime]=None
    while True:
        section("Serta — Main Menu")
        opts=[("1","Create New Project"),("2","Load Existing Project")]
        if runtime:opts.append(("3",f"Control Panel  [{C.BGREEN}{runtime.config.get('name','')}{C.RESET}]"))
        opts.append(("0","Exit"))
        choice=menu("What would you like to do?",opts)
        if choice=="1":
            cfg=create_project()
            if cfg:
                spinner("Initialising project",1.0);runtime=ServerRuntime(cfg)
                if confirm("Start server now?",default=True):runtime.start()
                run_control_panel(runtime)
        elif choice=="2":
            cfg=select_project()
            if cfg:
                spinner("Loading project",0.8);runtime=ServerRuntime(cfg)
                if confirm("Start server now?",default=True):runtime.start()
                run_control_panel(runtime)
        elif choice=="3" and runtime:run_control_panel(runtime)
        elif choice=="0":
            if runtime and runtime.running and confirm("Stop server before exit?",True):runtime.stop()
            print(f"\n  {C.BGREEN}Goodbye!{C.RESET}  Serta v3.2\n");sys.exit(0)
        else:warn("Invalid choice.")
        input(f"\n  {C.DIM}Press Enter…{C.RESET}")

if __name__=="__main__":
    main()
