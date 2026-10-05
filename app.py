import os
import re
import html
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="EnterprisePulse", page_icon=":material/hub:", layout="wide", initial_sidebar_state="expanded")

def secret(name):
    """Read from Streamlit secrets locally, or environment variables on Render."""
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name)

SUPABASE_URL = secret("SUPABASE_URL")
SUPABASE_KEY = secret("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase configuration is missing.")
    st.info("Set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml locally or as Render environment variables.")
    st.stop()

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
TODAY = date.today()

# ======================================================================
# Design system (presentation only)
# ======================================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
:root{--ink:#1B2430;--mute:#566273;--line:#DDE2E8;--line2:#EBEEF2;--bg:#F5F6F8;--surf:#FFFFFF;--acc:#1E4E8C;--accbg:#E8EFF8;--ok:#17693F;--warn:#9A5B00;--bad:#B42318}
.stApp{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg);font-size:14px}
h1,h2,h3,h4,p,label,button,input,textarea,select,a{font-family:inherit}
.stMarkdown p,label,[data-testid="stCaptionContainer"]{font-size:14px}
[data-testid="stCaptionContainer"]{color:var(--mute)}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{visibility:hidden}
header[data-testid="stHeader"]{background:transparent}
[data-testid="stMainBlockContainer"],.block-container{max-width:1360px;padding:1rem 2rem 4rem}
:focus-visible{outline:2px solid var(--acc)!important;outline-offset:2px}

/* Sidebar */
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
section[data-testid="stSidebar"][aria-expanded="true"]{min-width:248px;max-width:264px}
[data-testid="stSidebarNavLink"]{border-radius:6px;padding:.38rem .6rem;color:var(--ink);font-size:14px;transition:background .15s ease,color .15s ease}
[data-testid="stSidebarNavLink"]:hover{background:#EEF1F5}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:var(--accbg);color:var(--acc);font-weight:600}
[data-testid="stSidebarNavLink"] span{color:inherit}
[data-testid="stNavSectionHeader"],[data-testid="stSidebarNavSeparator"]{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
[data-testid="stNavSectionHeader"] span{color:var(--mute);font-size:11px;font-weight:600}
[data-testid="stSidebarUserContent"]{position:sticky;bottom:0;background:#fff;border-top:1px solid var(--line);padding-top:.75rem}

/* Controls */
.stButton>button,.stDownloadButton>button,.stLinkButton a,[data-testid="stPageLink"] a,[data-testid="stPopover"]>div>button{border-radius:6px;font-weight:500;font-size:14px;min-height:2.25rem;transition:background .15s ease,border-color .15s ease,color .15s ease}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:6px!important}
button[role="tab"]{font-size:14px;font-weight:500;color:var(--mute)}
button[role="tab"][aria-selected="true"]{color:var(--acc);font-weight:600}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:8px;overflow:hidden}
[data-testid="stChatMessage"]{background:transparent;padding:.75rem 0;border-bottom:1px solid var(--line2)}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:8px}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"]{gap:.35rem}

/* Content components */
.pt{font-size:26px;font-weight:600;letter-spacing:-.01em;line-height:1.25;margin:.25rem 0 .15rem}
.ps{color:var(--mute);font-size:14px;margin-bottom:.9rem}
.crumb{font-size:13px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.crumb b{color:var(--ink);font-weight:600}.crumb i{font-style:normal;padding:0 .35rem}
.sec{display:flex;align-items:baseline;justify-content:space-between;margin:1.4rem 0 .6rem;padding-bottom:.4rem;border-bottom:1px solid var(--line)}
.sec .n{font-size:16px;font-weight:600}.sec .c{font-size:12.5px;color:var(--mute)}
.kpis{display:flex;flex-wrap:wrap;background:#fff;border:1px solid var(--line);border-radius:8px;margin:.5rem 0 .25rem;overflow:hidden}
.kpi{flex:1 1 130px;padding:.7rem 1rem;border-right:1px solid var(--line2)}.kpi:last-child{border-right:0}
.kpi .l{font-size:12.5px;color:var(--mute);font-weight:500}.kpi .v{font-size:24px;font-weight:600;line-height:1.2;margin-top:2px}
.kpi.bad .v{color:var(--bad)}
.list{background:#fff;border:1px solid var(--line);border-radius:8px}
.li{display:flex;gap:.75rem;align-items:flex-start;padding:.6rem .9rem;border-bottom:1px solid var(--line2)}
.list .li:last-child{border-bottom:0}
.li .t{font-size:14px;font-weight:500;line-height:1.35;word-break:break-word}.li .m{font-size:12.5px;color:var(--mute);margin-top:1px}
.li .r{margin-left:auto;font-size:12.5px;color:var(--mute);white-space:nowrap;padding-left:.5rem}
.li.unread .t{font-weight:600}
.av{flex:none;width:28px;height:28px;border-radius:50%;background:#E3E8EF;color:#2F3B4C;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center}
.ud{flex:none;width:8px;height:8px;border-radius:50%;margin-top:.45rem;background:var(--acc)}.ud.off{background:transparent;border:1px solid #AEB7C4}
.bd{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;white-space:nowrap}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%}
.panel{background:#fff;border:1px solid var(--line);border-radius:8px;padding:.9rem 1rem;font-size:14px;line-height:1.55}
.kv{display:grid;grid-template-columns:104px 1fr;row-gap:.6rem;font-size:13.5px}.kv span{color:var(--mute)}.kv b{font-weight:500;word-break:break-word}
.empty{background:#fff;border:1px dashed #BAC3CF;border-radius:8px;padding:1.3rem 1rem;text-align:center}
.empty b{display:block;font-size:14px}.empty span{color:var(--mute);font-size:13px}
.bar{height:6px;background:#E3E8EF;border-radius:3px;overflow:hidden;margin-top:.35rem}.bar i{display:block;height:100%;background:var(--acc)}
.hd{display:flex;flex-wrap:wrap;gap:1.25rem;align-items:center;margin:.2rem 0 .6rem;font-size:13.5px;color:var(--mute)}.hd b{color:var(--ink);font-weight:500}
.tag{display:inline-block;border:1px solid var(--line);background:#fff;border-radius:4px;padding:.1rem .45rem;font-size:12.5px;margin:0 .35rem .35rem 0}
.tag em{font-style:normal;color:var(--mute);margin-right:.3rem}
.src{font-size:12.5px;color:var(--mute);margin-top:.5rem}
.src b{font-weight:600;color:var(--ink);margin-right:.4rem}
.brand{text-align:left;margin-bottom:1rem}.brand .pt{font-size:22px;margin:.6rem 0 0}
@media(max-width:768px){[data-testid="stMainBlockContainer"],.block-container{padding:.75rem 1rem 3rem}.kpi{flex-basis:45%}.pt{font-size:22px}.li .r{white-space:normal}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>""", unsafe_allow_html=True)

TABLES = ["departments","employees","projects","project_members","tasks","documents",
          "document_versions","issues","activities","notifications"]

@st.cache_data(ttl=15, show_spinner="Loading workspace data")
def load():
    return {t: pd.DataFrame(sb.table(t).select("*").execute().data) for t in TABLES}

def refresh():
    load.clear()

try:
    D = load()
except Exception:
    st.error("EnterprisePulse could not load workspace data. Check the Supabase connection and try again.")
    if st.button("Retry"):
        refresh(); st.rerun()
    st.stop()
EMP = D["employees"].set_index("id")
DEPT = D["departments"].set_index("id")["name"].to_dict()
PROJ = D["projects"].set_index("id")

def ename(i):
    return EMP.name.get(i, "Unassigned") if pd.notna(i) else "Company-wide"

def pname(i):
    return PROJ.name.get(i, "None") if pd.notna(i) else "None"

def tasks():
    t = D["tasks"].copy()
    t["due"] = pd.to_datetime(t["due"]).dt.date
    t["state"] = t.apply(lambda r: "Overdue" if r.status != "Completed" and r.due < TODAY else r.status, axis=1)
    return t

def health(pid):
    """Transparent rules: Critical if 3+ overdue tasks or an open critical issue.
    At Risk if any overdue task, or deadline within 14 days with progress under 80."""
    p = PROJ.loc[pid]
    if p.status == "completed":
        return "Completed"
    t = tasks(); t = t[t.project_id == pid]
    od = (t.state == "Overdue").sum()
    i = D["issues"]; crit = ((i.project_id == pid) & (i.priority == "Critical") & (i.status == "Open")).any()
    days = (pd.to_datetime(p.deadline).date() - TODAY).days
    if od >= 3 or crit:
        return "Critical"
    if od >= 1 or (days <= 14 and p.progress < 80):
        return "At Risk"
    return "On Track"

COL = {"On Track": "#2E8B57", "At Risk": "#D69E2E", "Critical": "#C53030", "Completed": "#8A94A0"}

def my_projects(u):
    if u.role == "admin":
        return list(PROJ.index)
    pm = D["project_members"]
    ids = set(pm[pm.employee_id == u.id].project_id) | set(PROJ[PROJ.manager_id == u.id].index)
    return list(ids)

def visible_docs(u):
    d = D["documents"]; mine = set(my_projects(u))
    def ok(r):
        if u.role == "admin" or r.uploader_id == u.id or r.access == "Company":
            return True
        if r.access == "Department":
            return r.dept_id == u.dept_id
        if r.access == "Project Team":
            return r.project_id in mine
        return False
    return d[d.apply(ok, axis=1)] if len(d) else d

def log(u, action, pid=None, did=None, notify=None):
    sb.table("activities").insert({"actor_id": int(u.id), "action": action, "project_id": pid, "document_id": did}).execute()
    if notify:
        sb.table("notifications").insert({"text": f"{u['name']} {action}", "project_id": pid}).execute()
    refresh()

# ======================================================================
# UI helpers (presentation only)
# ======================================================================
TXT = {"On Track": "#17693F", "At Risk": "#9A5B00", "Critical": "#B42318", "Completed": "#566273",
       "Overdue": "#B42318", "Blocked": "#B42318", "In Progress": "#1E4E8C", "To Do": "#566273",
       "High": "#9A5B00", "Medium": "#566273", "Low": "#566273", "Open": "#9A5B00"}
CATS = ["Policies", "SOPs", "Guidelines", "Reports", "Technical", "Financial", "Meeting Minutes"]

def esc(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return html.escape(str(x))

def initials(n):
    p = str(n).split()
    return (p[0][0] + p[-1][0]).upper() if len(p) > 1 else (p[0][:2].upper() if p else "?")

def fd(x):
    try:
        v = pd.to_datetime(x)
        return "" if pd.isna(v) else v.strftime("%d %b %Y")
    except Exception:
        return ""

def pn(i):
    return PROJ.name[i] if pd.notna(i) and i in PROJ.index else "No project"

def dn(i):
    return DEPT.get(i, "") if pd.notna(i) else ""

def tone(v):
    c = TXT.get(str(v))
    return f"color:{c};font-weight:600" if c else ""

def badge(s):
    s = str(s); c = COL.get(s) or TXT.get(s, "#8A94A0")
    return f"<span class='bd' style='color:{TXT.get(s, '#1B2430')}'><i class='dot' style='background:{c}'></i>{esc(s)}</span>"

def md(h):
    st.markdown(h, unsafe_allow_html=True)

def head(title, sub=""):
    md(f"<div class='pt'>{esc(title)}</div>" + (f"<div class='ps'>{esc(sub)}</div>" if sub else ""))

def sec(title, note=""):
    md(f"<div class='sec'><div class='n' role='heading' aria-level='3'>{esc(title)}</div><div class='c'>{esc(note)}</div></div>")

def empty(title, hint):
    md(f"<div class='empty'><b>{esc(title)}</b><span>{esc(hint)}</span></div>")

def kpis(items):
    cells = "".join(f"<div class='kpi{' bad' if bad else ''}'><div class='l'>{esc(l)}</div><div class='v'>{esc(v)}</div></div>" for l, v, bad in items)
    md(f"<div class='kpis'>{cells}</div>")

def li(title="", meta=(), right="", av=None, html_title=None, unread=None):
    lead = ""
    if av:
        lead = f"<div class='av' aria-hidden='true'>{esc(initials(av))}</div>"
    if unread is not None:
        lead = f"<div class='ud{'' if unread else ' off'}' title=\"{'Unread' if unread else 'Read'}\"></div>"
    m = " · ".join(esc(x) for x in meta if x not in (None, ""))
    t = html_title if html_title is not None else esc(title)
    return (f"<div class='li{' unread' if unread else ''}'>{lead}<div><div class='t'>{t}</div>"
            + (f"<div class='m'>{m}</div>" if m else "") + "</div>" + (f"<div class='r'>{right}</div>" if right else "") + "</div>")

def listbox(items, empty_title="Nothing to show", empty_hint=""):
    if not items:
        empty(empty_title, empty_hint); return
    md("<div class='list'>" + "".join(items) + "</div>")

def kv(pairs):
    md("<div class='panel'><div class='kv'>" + "".join(f"<span>{esc(k)}</span><b>{v}</b>" for k, v in pairs) + "</div></div>")

def stretch(fn, *a, **k):
    try:
        return fn(*a, width="stretch", **k)
    except Exception:
        return fn(*a, use_container_width=True, **k)

PROG = st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%d%%")
def DATEC(label):
    return st.column_config.DateColumn(label, format="DD MMM YYYY")

def plain(fr, cfg=None, tone_cols=()):
    obj = fr
    if tone_cols:
        try:
            obj = fr.style.map(tone, subset=list(tone_cols))
        except Exception:
            obj = fr
    stretch(st.dataframe, obj, hide_index=True, column_config={**(cfg or {}), "_id": None})

def pick(state, fr, labelcol, cfg=None, tone_cols=()):
    """Selectable table. Selecting a row (or choosing it below) stores its id under open:<state>."""
    fr = fr.reset_index(drop=True)
    n = st.session_state.get(f"n:{state}", 0)
    obj = fr
    if tone_cols:
        try:
            obj = fr.style.map(tone, subset=list(tone_cols))
        except Exception:
            obj = fr
    ev = stretch(st.dataframe, obj, hide_index=True, column_config={**(cfg or {}), "_id": None},
                 on_select="rerun", selection_mode="single-row", key=f"t:{state}:{n}")
    rows = list(ev.selection.rows) if ev is not None else []
    sel = int(rows[0]) if rows else None
    labels = list(fr[labelcol])
    j = st.selectbox("Open a record", labels, index=None, placeholder="Select a row above, or choose a record to open here",
                     label_visibility="collapsed", key=f"j:{state}:{n}")
    if j is not None:
        sel = labels.index(j)
    if sel is not None:
        st.session_state[f"open:{state}"] = fr.loc[sel, "_id"]
        st.session_state[f"n:{state}"] = n + 1
        st.rerun()

def opened(state):
    return st.session_state.get(f"open:{state}")

def close(state):
    st.session_state[f"open:{state}"] = None
    st.rerun()

def back(state, label):
    if st.button(label, icon=":material/arrow_back:", type="tertiary", key=f"back:{state}"):
        close(state)

def _go_search():
    st.session_state["sq_pending"] = st.session_state.get("gq", "")
    st.session_state["gq"] = ""
    st.session_state["goto_search"] = True

def my_notes():
    n = D["notifications"]
    if n.empty:
        return n
    return n[n.employee_id.isna() | (n.employee_id == U.id)]

def top(*crumbs, search=True):
    """Application header: breadcrumb, global search, notifications, help, profile."""
    msg = st.session_state.pop("flash", None)
    if msg:
        st.toast(msg)
    n = my_notes()
    read = st.session_state.get("read_notes", set())
    unread = 0 if n.empty else int((~n["id"].isin(read)).sum())
    a, b, c = st.columns([3.2, 4, 3.8], vertical_alignment="center")
    with a:
        parts = [f"<b>{esc(x)}</b>" if k == len(crumbs) - 1 else esc(x) for k, x in enumerate(crumbs)]
        md("<div class='crumb'>" + "<i>/</i>".join(parts) + "</div>")
    with b:
        if search:
            st.text_input("Global search", key="gq", placeholder="Search projects, documents, people   Ctrl + K",
                          label_visibility="collapsed", on_change=_go_search)
            if st.session_state.pop("goto_search", False):
                st.switch_page(PG["Search"])
    with c:
        x, y, z = st.columns([1.7, 1, 0.45], vertical_alignment="center")
        with x:
            st.page_link(PG["Notifications"], label=f"Notifications ({unread})" if unread else "Notifications", icon=":material/notifications:")
        with y:
            with st.popover("Help", icon=":material/help:"):
                st.markdown("**Shortcuts**\n\nPress Ctrl + K to jump to search.\n\n**Need access?**\n\nContact your administrator for access changes or password resets.")
        with z:
            md(f"<div class='av' title='{esc(U['name'])}'>{esc(initials(U['name']))}</div>")

# ======================================================================
# Authentication (logic unchanged)
# ======================================================================
def login():
    _, c, _ = st.columns([1, 1.1, 1])
    with c:
        st.write(""); st.write("")
        md("<div class='brand'><div class='pt'>EnterprisePulse</div><div class='ps'>Enterprise Knowledge Warehouse</div></div>")
        with st.container(border=True):
            md("<div style='font-size:18px;font-weight:600;margin-bottom:.15rem'>Sign in</div><div class='ps' style='margin-bottom:.5rem'>Use your work account to continue.</div>")
            with st.form("login", border=False):
                email = st.text_input("Employee ID or email")
                pw = st.text_input("Password", type="password")
                go = stretch(st.form_submit_button, "Sign in", type="primary")
            if go:
                try:
                    sb.auth.sign_in_with_password({"email": email, "password": pw})
                    row = EMP[EMP.email == email]
                    if row.empty:
                        st.error("Your account is not linked to an employee record. Ask an admin to add it.")
                    else:
                        st.session_state.uid = int(row.index[0]); st.rerun()
                except Exception:
                    st.error("Email or password is incorrect.")
        st.caption("Forgot your password? Contact your administrator to reset it.")

if "uid" not in st.session_state:
    login(); st.stop()
U = EMP.loc[st.session_state.uid].copy(); U["id"] = st.session_state.uid

# ======================================================================
# Pages
# ======================================================================
def doc_frame(d):
    if d is None or len(d) == 0:
        return pd.DataFrame(columns=["_id", "Document", "Category", "Project", "Owner", "Department", "Version", "Updated", "Access"])
    return pd.DataFrame({"_id": d["id"].values, "Document": d["name"].values, "Category": d["category"].values,
        "Project": [pn(x) for x in d.project_id], "Owner": [ename(x) for x in d.uploader_id],
        "Department": [dn(x) for x in d.dept_id], "Version": d["version"].values,
        "Updated": pd.to_datetime(d["created"]).dt.date.values, "Access": d["access"].values})

DOC_CFG = {"Updated": DATEC("Updated")}

def doc_detail(did, state):
    d = D["documents"]; r = d[d["id"] == did]
    if r.empty:
        close(state); return
    r = r.iloc[0]
    back(state, "Back to documents")
    head(r["name"], f"{r.category} · version {r.version}")
    left, right = st.columns([2.2, 1])
    with left:
        sec("Description")
        md(f"<div class='panel'>{esc(r.description) or 'No description was added for this document.'}</div>")
        if r.path:
            st.link_button("Download file", sb.storage.from_("documents").get_public_url(r.path), icon=":material/download:")
        else:
            st.caption("No file is attached to this record.")
        sec("Version history")
        v = D["document_versions"]; v = v[v.document_id == r["id"]].sort_values("created", ascending=False)
        listbox([li(f"{x.version}" + (" (latest)" if x.version == r.version else ""), [x.note], fd(x.created)) for _, x in v.iterrows()],
                "No version history", "Versions are recorded each time a new file is uploaded.")
    with right:
        sec("Record")
        kv([("Owner", esc(ename(r.uploader_id))), ("Project", esc(pn(r.project_id))), ("Department", esc(dn(r.dept_id))),
            ("Access", esc(r.access)), ("Created", esc(fd(r.created))), ("Version", esc(r.version))])
    a = D["activities"]; a = a[a.document_id == r["id"]].sort_values("at", ascending=False)
    sec("Activity")
    listbox([li(f"{ename(x.actor_id)} {x.action}", [], fd(x.at), av=ename(x.actor_id)) for _, x in a.iterrows()],
            "No activity yet", "Uploads and changes to this document will appear here.")
    rel = visible_docs(U)
    rel = rel[(rel["id"] != r["id"]) & ((rel.category == r.category) | ((rel.project_id == r.project_id) & pd.notna(r.project_id)))]
    sec("Related documents", f"{len(rel)}")
    listbox([li(x["name"], [x.category, pn(x.project_id), x.version]) for _, x in rel.head(6).iterrows()],
            "No related documents", "Documents in the same category or project appear here.")

def documents():
    top("Knowledge", "Documents")
    sel = opened("doc")
    if sel is not None:
        doc_detail(sel, "doc"); return
    head("Documents", "Company documents you have access to. Select a row to open the record.")
    with st.popover("Upload document", icon=":material/upload:", type="primary"):
        f = st.file_uploader("File")
        name = st.text_input("Document name", value=f.name if f else "", help="Uploading a file with an existing name creates a new version.")
        cat = st.selectbox("Category ", CATS)
        dep = st.selectbox("Department ", list(DEPT.values()), index=int(U.dept_id) - 1)
        pr = st.selectbox("Project", ["None"] + [PROJ.name[i] for i in my_projects(U)])
        desc = st.text_area("Description", help="Briefly describe what changed or what this document covers.")
        acc = st.selectbox("Access level", ["Company", "Department", "Project Team", "Restricted"])
        if st.button("Upload document", type="primary"):
            if not f or not name:
                st.error("Choose a file and enter a document name.")
            else:
                pid = None if pr == "None" else int(PROJ[PROJ.name == pr].index[0])
                did_ = [k for k, v in DEPT.items() if v == dep][0]
                safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", f.name).strip() or "document"
                path = f"{TODAY}/{safe_name}"
                sb.storage.from_("documents").upload(path, f.getvalue(), {"upsert": "true"})
                old = D["documents"][D["documents"].name == name]
                if len(old):
                    major, minor = old.iloc[0].version.lstrip("v").split(".")
                    ver = f"v{major}.{int(minor)+1}"
                    sb.table("documents").update({"version": ver, "path": path, "description": desc}).eq("id", int(old.iloc[0]["id"])).execute()
                    docid = int(old.iloc[0]["id"])
                else:
                    ver = "v1.0"
                    docid = sb.table("documents").insert({"name": name, "category": cat, "dept_id": did_, "project_id": pid,
                        "uploader_id": int(U.id), "access": acc, "description": desc, "path": path, "version": ver}).execute().data[0]["id"]
                sb.table("document_versions").insert({"document_id": docid, "version": ver, "note": desc or "Uploaded"}).execute()
                log(U, f"uploaded {name}", pid, docid, notify=True)
                st.session_state["flash"] = "Document uploaded."; st.rerun()
    doc_browser_body("doc")

def doc_browser_body(state, fixed_cat=None):
    d = visible_docs(U)
    if fixed_cat is not None and len(d):
        d = d[d.category == fixed_cat]
    c = st.columns([2.2, 1.2, 1.2, 1.2, 1.2, 1], vertical_alignment="bottom")
    q = c[0].text_input("Filter", placeholder="Filter by name or description", label_visibility="collapsed", key=f"q:{state}")
    cats = ["All categories"] + (sorted(d.category.unique()) if len(d) else [])
    cat = c[1].selectbox("Category", cats, label_visibility="collapsed", key=f"c:{state}")
    dep = c[2].selectbox("Department", ["All departments"] + sorted(DEPT.values()), label_visibility="collapsed", key=f"d:{state}")
    prj = c[3].selectbox("Project", ["All projects"] + sorted(set(PROJ.name)), label_visibility="collapsed", key=f"p:{state}")
    acc = c[4].selectbox("Access", ["All access levels", "Company", "Department", "Project Team", "Restricted"], label_visibility="collapsed", key=f"a:{state}")
    srt = c[5].selectbox("Sort", ["Newest", "Name"], label_visibility="collapsed", key=f"s:{state}")
    if q and len(d):
        d = d[d["name"].fillna("").str.contains(q, case=False, na=False) | d["description"].fillna("").str.contains(q, case=False, na=False)]
    if cat != "All categories" and len(d): d = d[d.category == cat]
    if dep != "All departments" and len(d): d = d[d.dept_id.map(DEPT) == dep]
    if prj != "All projects" and len(d): d = d[d.project_id.map(pn) == prj]
    if acc != "All access levels" and len(d): d = d[d.access == acc]
    if len(d):
        d = d.sort_values("created", ascending=False) if srt == "Newest" else d.sort_values("name")
    st.caption(f"{len(d)} document{'s' if len(d) != 1 else ''}")
    if len(d) == 0:
        empty("No documents found", "Try changing your filters or upload a new document.")
    else:
        pick(state, doc_frame(d), "Document", DOC_CFG)

def policies():
    top("Knowledge", "Policies")
    if opened("pol") is not None:
        doc_detail(opened("pol"), "pol"); return
    head("Policies", "Official company policies.")
    doc_browser_body("pol", "Policies")

def reports():
    top("Knowledge", "Reports")
    if opened("rep") is not None:
        doc_detail(opened("rep"), "rep"); return
    head("Reports", "Project and operational reports.")
    doc_browser_body("rep", "Reports")

def dashboard():
    top("Home", "Dashboard")
    ids = my_projects(U); t = tasks()
    mt = t[(t.assignee_id == U.id) & (t.status != "Completed")]
    notes = my_notes(); read = st.session_state.get("read_notes", set())
    unread = 0 if notes.empty else int((~notes["id"].isin(read)).sum())
    od = int((mt.state == "Overdue").sum())
    head(f"{'Good morning' if pd.Timestamp.now().hour < 12 else 'Good afternoon'}, {U['name'].split()[0]}", "Here is what is happening across your projects today.")
    kpis([("Projects", len(ids), False), ("Active tasks", len(mt), False), ("Documents", len(visible_docs(U)), False),
          ("Unread notifications", unread, False), ("Pending actions", od, od > 0)])
    # Attention required: only items needing action
    hs = {i: health(i) for i in ids}
    crit = D["issues"]; crit = crit[crit.project_id.isin(ids) & (crit.priority == "Critical") & (crit.status == "Open")]
    att = []
    for _, r in mt[mt.state == "Overdue"].iterrows():
        att.append(li(r.title, [pn(r.project_id), f"due {fd(r.due)}"], badge("Overdue")))
    for _, r in mt[mt.state == "Blocked"].iterrows():
        att.append(li(r.title, [pn(r.project_id), f"due {fd(r.due)}"], badge("Blocked")))
    for _, r in crit.iterrows():
        att.append(li(r.title, [pn(r.project_id), f"owner {ename(r.owner_id)}"], badge("Critical")))
    for i, h in hs.items():
        if h in ("At Risk", "Critical"):
            att.append(li(PROJ.name[i], [f"due {fd(PROJ.deadline[i])}", f"{PROJ.progress[i]}% complete"], badge(h)))
    sec("Attention required", f"{len(att)} item{'s' if len(att) != 1 else ''}")
    listbox(att, "Nothing needs your attention", "Overdue work, blocked tasks, critical issues and at risk projects will appear here.")
    a, b = st.columns([3, 2], gap="large")
    iss = D["issues"]
    with a:
        sec("My projects", f"{len(ids)}")
        rows = []
        for i in ids:
            oi = int(((iss.project_id == i) & (iss.status == "Open")).sum())
            rows.append(li(html_title=f"<b>{esc(PROJ.name[i])}</b>", title="", meta=[f"{PROJ.progress[i]}% complete", f"due {fd(PROJ.deadline[i])}", f"{oi} open issue{'s' if oi != 1 else ''}"],
                           right=badge(health(i))))
        listbox(rows, "You are not on any projects yet", "Projects you manage or belong to will appear here.")
        sec("Upcoming deadlines")
        up = t[(t.status != "Completed") & (t.project_id.isin(ids))].sort_values("due").head(6)
        listbox([li(r.title, [pn(r.project_id), ename(r.assignee_id), r.priority], f"<span style='{tone(r.state) if r.state == 'Overdue' else ''}'>{esc(fd(r.due))}</span>") for _, r in up.iterrows()],
                "No upcoming deadlines", "Open tasks with due dates will appear here.")
    with b:
        sec("Recent activity")
        act = D["activities"].sort_values("at", ascending=False).head(7)
        listbox([li(f"{ename(r.actor_id)} {r.action}", [pn(r.project_id) if pd.notna(r.project_id) else "Company-wide"], fd(r.at), av=ename(r.actor_id)) for _, r in act.iterrows()],
                "No recent activity", "Uploads and changes will appear here.")
        sec("Recently added documents")
        vd = visible_docs(U)
        vd = vd.sort_values("created", ascending=False).head(4) if len(vd) else vd
        listbox([li(r["name"], [r.category, ename(r.uploader_id), r.version], fd(r.created)) for _, r in vd.iterrows()],
                "No documents yet", "Uploaded documents will appear here.")

STOP = set("the what who is are for and status of in on with me show find latest any all".split())

def search(q, u):
    words = [w for w in re.findall(r"\w+", q.lower()) if w not in STOP and len(w) > 1]
    hit = lambda *v: sum(w in " ".join(map(str, v)).lower() for w in words)
    ids = set(my_projects(u)); t = tasks(); t = t[t.project_id.isin(ids)]
    P = [i for i in ids if hit(PROJ.name[i]) > 0]
    tk = t[t.apply(lambda r: hit(r.title, r.description, r.state, pname(r.project_id), ename(r.assignee_id)) > 0 or r.project_id in P, axis=1)]
    if "overdue" in q.lower():
        tk = t[t.state == "Overdue"]
    vd = visible_docs(u)
    dc = vd[vd.apply(lambda r: hit(r["name"], r.category, r.description, pname(r.project_id)) > 0 or r.project_id in P, axis=1)] if len(vd) else vd
    mem = D["project_members"]
    pe = set(mem[mem.project_id.isin(P)].employee_id)
    em = [i for i in EMP.index if hit(EMP.name[i], EMP.designation[i], " ".join(EMP.skills[i] or []), DEPT.get(EMP.dept_id[i])) > 0 or i in pe]
    iss = D["issues"]; iss = iss[iss.project_id.isin(P)] if P else iss.iloc[0:0]
    return P, tk, dc, em, iss

def search_page():
    top("Home", "Search", search=False)
    head("Search", "Search across projects, documents, people, tasks and issues.")
    if "sq_pending" in st.session_state:
        st.session_state["sq"] = st.session_state.pop("sq_pending")
    q = st.text_input("Search", key="sq", placeholder="Search anything in EnterprisePulse", label_visibility="collapsed")
    if not q:
        st.caption("Try: Project Alpha, leave policy, Python, overdue tasks")
        return
    P, tk, dc, em, iss = search(q, U)
    total = len(P) + len(tk) + len(dc) + len(em) + len(iss)
    if not total:
        empty("No results", "Check the spelling or search by project, person or document name."); return
    st.caption(f"{total} result{'s' if total != 1 else ''} for \"{q}\"")
    if P:
        sec("Projects", f"{len(P)}")
        listbox([li(PROJ.name[i], ["Project", f"Manager {ename(PROJ.manager_id[i])}", f"{PROJ.progress[i]}% complete", f"due {fd(PROJ.deadline[i])}"], badge(health(i))) for i in P])
    if len(dc):
        sec("Documents and policies", f"{len(dc)}")
        listbox([li(r["name"], [r.category, pn(r.project_id), f"owner {ename(r.uploader_id)}", r.version, f"updated {fd(r.created)}"]) for _, r in dc.iterrows()])
    if em:
        sec("Employees", f"{len(em)}")
        listbox([li(EMP.name[i], [EMP.designation[i], DEPT.get(EMP.dept_id[i])], av=EMP.name[i]) for i in em])
    if len(tk):
        sec("Tasks", f"{len(tk)}")
        listbox([li(r.title, [pn(r.project_id), ename(r.assignee_id), f"due {fd(r.due)}"], badge(r.state)) for _, r in tk.iterrows()])
    if len(iss):
        sec("Issues", f"{len(iss)}")
        listbox([li(r.title, [pn(r.project_id), f"owner {ename(r.owner_id)}", f"opened {fd(r.created)}"], badge(r.priority) + " · " + esc(r.status)) for _, r in iss.iterrows()])

def kb():
    top("Knowledge", "Knowledge Base")
    head("Knowledge Base", "Company policies, procedures and project knowledge in one place.")
    d = visible_docs(U)
    left, right = st.columns([1, 3], gap="large")
    with left:
        sec("Categories")
        cat = st.radio("Category", ["All"] + CATS, label_visibility="collapsed",
                       format_func=lambda c: f"{c} ({len(d) if c == 'All' else (int((d.category == c).sum()) if len(d) else 0)})")
    with right:
        sub = d if cat == "All" or not len(d) else d[d.category == cat]
        if opened("kb") is not None:
            doc_detail(opened("kb"), "kb"); return
        if cat == "All" and len(sub):
            sec("Recently updated")
            listbox([li(r["name"], [r.category, dn(r.dept_id), ename(r.uploader_id), r.version, r.access], fd(r.created)) for _, r in sub.sort_values("created", ascending=False).head(4).iterrows()])
            vc = D["document_versions"]
            if len(vc):
                cnt = vc.groupby("document_id").size().sort_values(ascending=False)
                pop = sub[sub["id"].isin(cnt.index[:3])]
                if len(pop):
                    sec("Most revised")
                    listbox([li(r["name"], [r.category, f"{int(cnt[r['id']])} versions", r.version]) for _, r in pop.iterrows()])
        sec(cat if cat != "All" else "All documents", f"{len(sub)}")
        if len(sub) == 0:
            empty("No documents in this category yet", "Documents uploaded with this category will appear here.")
        else:
            pick("kb", doc_frame(sub.sort_values("created", ascending=False)), "Document", DOC_CFG)

def proj_frame(ids):
    t = tasks(); iss = D["issues"]; rows = []
    for i in ids:
        rows.append({"_id": i, "Project": PROJ.name[i], "Manager": ename(PROJ.manager_id[i]), "Status": health(i), "Progress": int(PROJ.progress[i]),
                     "Due date": pd.to_datetime(PROJ.deadline[i]).date(),
                     "Open tasks": int(((t.project_id == i) & (t.status != "Completed")).sum()),
                     "Issues": int(((iss.project_id == i) & (iss.status == "Open")).sum())})
    return pd.DataFrame(rows)

def project_detail(pid):
    p = PROJ.loc[pid]; t = tasks(); t = t[t.project_id == pid]
    iss = D["issues"]; iss = iss[iss.project_id == pid]
    top("Projects", p["name"])
    back("proj", "Back to projects")
    head(p["name"])
    md(f"<div class='hd'>{badge(health(pid))}<span>Manager <b>{esc(ename(p.manager_id))}</b></span><span>Progress <b>{p.progress}%</b></span><span>Due <b>{esc(fd(p.deadline))}</b></span><span>Department <b>{esc(dn(p.dept_id))}</b></span></div>")
    kpis([("Progress", f"{p.progress}%", False), ("Due date", fd(p.deadline), False), ("Budget used", f"{int(p.spent/p.budget*100)}%", False),
          ("Tasks", len(t), False), ("Overdue", int((t.state == "Overdue").sum()), int((t.state == "Overdue").sum()) > 0), ("Open issues", int((iss.status == "Open").sum()), False)])
    tabs = st.tabs(["Overview", "Tasks", "Team", "Documents", "Issues", "Activity"])
    with tabs[0]:
        md(f"<div class='bar' role='progressbar' aria-valuenow='{int(p.progress)}' aria-valuemin='0' aria-valuemax='100'><i style='width:{int(p.progress)}%'></i></div>")
        a, b = st.columns(2, gap="large")
        with a:
            sec("Upcoming deadlines")
            up = t[t.status != "Completed"].sort_values("due").head(5)
            listbox([li(r.title, [ename(r.assignee_id), r.priority], esc(fd(r.due))) for _, r in up.iterrows()], "No open tasks", "Everything on this project is complete.")
            sec("Open issues")
            oi = iss[iss.status == "Open"]
            listbox([li(r.title, [f"owner {ename(r.owner_id)}", f"opened {fd(r.created)}"], badge(r.priority)) for _, r in oi.iterrows()], "No open issues", "Issues raised on this project will appear here.")
        with b:
            sec("Recent activity")
            ac = D["activities"]; ac = ac[ac.project_id == pid].sort_values("at", ascending=False).head(5)
            listbox([li(f"{ename(r.actor_id)} {r.action}", [], fd(r.at), av=ename(r.actor_id)) for _, r in ac.iterrows()], "No activity yet", "Changes to this project will appear here.")
        st.caption("Status rules: Critical if 3 or more tasks are overdue or a critical issue is open. At Risk if any task is overdue, or the deadline is within 14 days and progress is under 80%.")
    with tabs[1]:
        if t.empty:
            empty("No tasks yet", "Tasks added to this project will appear here.")
        else:
            plain(task_frame(t.sort_values("due")), {"Due date": DATEC("Due date")}, ("Status", "Priority"))
        if U.role in ("manager", "admin") and len(t):
            md("<div class='sec'><div class='n'>Update a task</div></div>")
            a, b, c2 = st.columns([3, 2, 1], vertical_alignment="bottom")
            tid = a.selectbox("Task", t["id"], format_func=lambda i: t[t["id"] == i].title.iloc[0])
            ns = b.selectbox("Status", ["To Do", "In Progress", "Blocked", "Completed"])
            if c2.button("Update task", type="primary"):
                sb.table("tasks").update({"status": ns}).eq("id", int(tid)).execute()
                log(U, f"updated a task to {ns} on {p['name']}", int(pid), None, notify=True)
                st.session_state["flash"] = "Task updated."; st.rerun()
    with tabs[2]:
        m = D["project_members"]; m = m[m.project_id == pid].employee_id
        listbox([li(EMP.name[e], [EMP.designation[e], dn(EMP.dept_id[e]), f"{len(t[t.assignee_id == e])} tasks on this project"], "Manager" if e == p.manager_id else "Member", av=EMP.name[e]) for e in m],
                "No team members", "Members added to this project will appear here.")
    with tabs[3]:
        d = visible_docs(U); d = d[d.project_id == pid] if len(d) else d
        if len(d) == 0:
            empty("No documents linked to this project", "Upload a document and link it to this project.")
        else:
            plain(doc_frame(d), DOC_CFG)
    with tabs[4]:
        if iss.empty:
            empty("No issues recorded", "Issues raised on this project will appear here.")
        else:
            plain(pd.DataFrame({"Issue": iss.title.values, "Priority": iss.priority.values, "Status": iss.status.values,
                                "Owner": [ename(x) for x in iss.owner_id], "Opened": pd.to_datetime(iss.created).dt.date.values}),
                  {"Opened": DATEC("Opened")}, ("Priority", "Status"))
    with tabs[5]:
        a = D["activities"]; a = a[a.project_id == pid].sort_values("at", ascending=False)
        listbox([li(f"{ename(r.actor_id)} {r.action}", [], esc(str(r.at)[:16].replace("T", " ")), av=ename(r.actor_id)) for _, r in a.iterrows()],
                "No activity yet", "Changes to this project will appear here.")

def task_frame(t):
    return pd.DataFrame({"_id": t["id"].values, "Task": t.title.values, "Project": [pn(x) for x in t.project_id], "Assignee": [ename(x) for x in t.assignee_id],
                         "Priority": t.priority.values, "Status": t.state.values, "Due date": t.due.values})

def projects():
    sel = opened("proj")
    if sel is not None and sel in PROJ.index and sel in my_projects(U):
        project_detail(sel); return
    top("Work", "Projects")
    head("Projects", "Projects you manage or belong to. Select a row to open the project.")
    ids = my_projects(U)
    if not ids:
        empty("You are not on any projects yet", "Projects you manage or belong to will appear here."); return
    c = st.columns([2.5, 1.3, 1.3], vertical_alignment="bottom")
    q = c[0].text_input("Filter projects", placeholder="Filter by project or manager", label_visibility="collapsed")
    stt = c[1].selectbox("Status", ["All statuses", "On Track", "At Risk", "Critical", "Completed"], label_visibility="collapsed")
    fr = proj_frame(ids)
    if q:
        fr = fr[fr.Project.str.contains(q, case=False) | fr.Manager.str.contains(q, case=False)]
    if stt != "All statuses":
        fr = fr[fr.Status == stt]
    st.caption("Click a column header to sort.")
    if fr.empty:
        empty("No projects match", "Try changing your filters.")
    else:
        pick("proj", fr, "Project", {"Progress": PROG, "Due date": DATEC("Due date")}, ("Status",))

def tasks_page():
    top("Work", "Tasks")
    head("Tasks", "Tasks across your projects.")
    ids = my_projects(U); t = tasks(); t = t[t.project_id.isin(ids)]
    views = {"All": t, "My Tasks": t[t.assignee_id == U.id], "Overdue": t[t.state == "Overdue"], "Blocked": t[t.state == "Blocked"], "Completed": t[t.state == "Completed"]}
    tabs = st.tabs([f"{k} ({len(v)})" for k, v in views.items()])
    for tab, (k, v) in zip(tabs, views.items()):
        with tab:
            if v.empty:
                empty("No tasks here", "Nothing matches this view right now.")
            else:
                plain(task_frame(v.sort_values("due")), {"Due date": DATEC("Due date")}, ("Status", "Priority"))

def issues_page():
    top("Work", "Issues")
    head("Issues", "Open and resolved issues across your projects.")
    ids = my_projects(U); iss = D["issues"]; iss = iss[iss.project_id.isin(ids)] if len(iss) else iss
    if iss.empty:
        empty("No issues recorded", "Issues raised on your projects will appear here."); return
    iss = iss.assign(_o=iss.priority.map({"Critical": 0, "High": 1, "Medium": 2, "Low": 3}).fillna(4)).sort_values(["_o", "created"])
    plain(pd.DataFrame({"Issue": iss.title.values, "Project": [pn(x) for x in iss.project_id], "Priority": iss.priority.values, "Status": iss.status.values,
                        "Owner": [ename(x) for x in iss.owner_id], "Opened": pd.to_datetime(iss.created).dt.date.values}),
          {"Opened": DATEC("Opened")}, ("Priority", "Status"))

def emp_detail(i):
    top("People", "Employees", EMP.name[i])
    back("emp", "Back to employees")
    head(EMP.name[i], f"{EMP.designation[i]} · {dn(EMP.dept_id[i])}")
    mem = D["project_members"]; pids = list(mem[mem.employee_id == i].project_id)
    t = tasks(); t = t[t.assignee_id == i]
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        sec("Projects", f"{len(pids)}")
        listbox([li(PROJ.name[x], [f"{PROJ.progress[x]}% complete", f"due {fd(PROJ.deadline[x])}"], badge(health(x))) for x in pids], "No projects", "This employee is not on any project.")
        sec("Tasks", f"{len(t)}")
        if t.empty: empty("No tasks assigned", "Tasks assigned to this employee will appear here.")
        else: plain(task_frame(t.sort_values("due")), {"Due date": DATEC("Due date")}, ("Status", "Priority"))
        sec("Documents")
        d = D["documents"]; d = d[d.uploader_id == i]
        vis = set(visible_docs(U)["id"]) if len(visible_docs(U)) else set()
        d = d[d["id"].isin(vis)] if len(d) else d
        listbox([li(r["name"], [r.category, r.version], fd(r.created)) for _, r in d.iterrows()], "No documents", "Documents uploaded by this employee that you can access appear here.")
        sec("Recent activity")
        a = D["activities"]; a = a[a.actor_id == i].sort_values("at", ascending=False).head(6)
        listbox([li(r.action, [pn(r.project_id) if pd.notna(r.project_id) else "Company-wide"], fd(r.at)) for _, r in a.iterrows()], "No recent activity", "")
    with right:
        sec("Profile")
        sk = "".join(f"<span class='tag'>{esc(s)}</span>" for s in (EMP.skills[i] or []))
        kv([("Name", esc(EMP.name[i])), ("Role", esc(EMP.designation[i])), ("Access", esc(str(EMP.role[i]).title())), ("Department", esc(dn(EMP.dept_id[i]))), ("Email", esc(EMP.email[i]))])
        if sk: md(f"<div style='margin-top:.75rem'>{sk}</div>")

def employees():
    sel = opened("emp")
    if sel is not None and sel in EMP.index:
        emp_detail(sel); return
    top("People", "Employees")
    head("Employees", "Company directory. Select a row to open a profile.")
    mem = D["project_members"]
    c = st.columns([2.5, 1.3, 1.3, 1.3], vertical_alignment="bottom")
    q = c[0].text_input("Search employees", placeholder="Name, department, role, skill or project", label_visibility="collapsed")
    dep = c[1].selectbox("Department", ["All departments"] + sorted(DEPT.values()), label_visibility="collapsed")
    rl = c[2].selectbox("Role", ["All roles"] + sorted(set(EMP.designation)), label_visibility="collapsed")
    pj = c[3].selectbox("Project", ["All projects"] + sorted(set(PROJ.name)), label_visibility="collapsed")
    rows = []
    for i in EMP.index:
        prj = [PROJ.name[x] for x in mem[mem.employee_id == i].project_id]
        blob = f"{EMP.name[i]} {DEPT.get(EMP.dept_id[i])} {EMP.designation[i]} {' '.join(EMP.skills[i] or [])} {' '.join(prj)}".lower()
        if q.lower() in blob and (dep == "All departments" or DEPT.get(EMP.dept_id[i]) == dep) and (rl == "All roles" or EMP.designation[i] == rl) and (pj == "All projects" or pj in prj):
            open_t = int(((tasks().assignee_id == i) & (tasks().status != "Completed")).sum())
            rows.append({"_id": i, "Name": EMP.name[i], "Role": EMP.designation[i], "Department": DEPT.get(EMP.dept_id[i], ""), "Projects": ", ".join(prj) or "None",
                         "Skills": ", ".join(EMP.skills[i] or []), "Open tasks": open_t})
    if not rows:
        empty("No employees found", "Try a different name, skill or filter."); return
    st.caption(f"{len(rows)} employee{'s' if len(rows) != 1 else ''}")
    pick("emp", pd.DataFrame(rows), "Name")

def departments():
    top("People", "Departments")
    head("Departments", "Teams and their current work.")
    mem = D["project_members"]; rows = []
    for did, name in DEPT.items():
        e = EMP[EMP.dept_id == did]
        pj = PROJ[PROJ.dept_id == did]
        rows.append({"Department": name, "Employees": len(e), "Projects": len(pj), "Active projects": int((pj.status != "completed").sum()),
                     "Head": ", ".join(e[e.role.isin(["manager", "admin"])].name) or "None"})
    plain(pd.DataFrame(rows))
    sec("Members")
    pick_d = st.selectbox("Department", list(DEPT.values()), label_visibility="collapsed")
    did = [k for k, v in DEPT.items() if v == pick_d][0]
    e = EMP[EMP.dept_id == did]
    listbox([li(e.name[i], [e.designation[i], ", ".join(e.skills[i] or [])], av=e.name[i]) for i in e.index], "No employees in this department", "")

def notifications():
    top("Communication", "Notifications")
    head("Notifications", "Updates from your projects and documents.")
    n = my_notes()
    if n.empty:
        empty("You are all caught up", "New notifications will appear here."); return
    n = n.sort_values("created", ascending=False)
    read = st.session_state.setdefault("read_notes", set())
    a, _ = st.columns([1, 4])
    if a.button("Mark all as read", icon=":material/done_all:"):
        read.update(n["id"]); st.rerun()
    cr = pd.to_datetime(n["created"])
    try:
        cr = cr.dt.tz_localize(None)
    except TypeError:
        cr = cr.dt.tz_convert(None)
    dd = cr.dt.date
    groups = [("Today", n[dd == TODAY]), ("Yesterday", n[dd == TODAY - timedelta(days=1)]), ("Earlier", n[dd < TODAY - timedelta(days=1)])]
    for title, g in groups:
        if g.empty:
            continue
        sec(title, f"{len(g)}")
        for _, r in g.iterrows():
            un = r["id"] not in read
            c1, c2 = st.columns([9, 1.6], vertical_alignment="center")
            with c1:
                md("<div class='list'>" + li(r.text, [pn(r.project_id) if pd.notna(r.project_id) else "Company-wide"], esc(str(r.created)[:16].replace("T", " ")), unread=un) + "</div>")
            with c2:
                if un and st.button("Mark as read", key=f"rd{r['id']}", type="tertiary"):
                    read.add(r["id"]); st.rerun()

def activity(admin=False):
    top("Communication", "Audit Log" if admin else "Activity")
    head("Audit Log" if admin else "Activity", "Chronological record of changes." )
    a = D["activities"]
    if not admin and len(a):
        a = a[a.project_id.isna() | a.project_id.isin(my_projects(U))]
    if a.empty:
        empty("No activity yet", "Uploads and changes will appear here."); return
    a = a.sort_values("at", ascending=False)
    plain(pd.DataFrame({"Time": pd.to_datetime(a["at"]).dt.strftime("%d %b %Y %H:%M").values, "User": [ename(x) for x in a.actor_id],
                        "Action": a.action.values, "Project": [pn(x) for x in a.project_id]}))

def analytics():
    top("Insights", "Analytics")
    head("Analytics", "Reporting across your projects.")
    ids = my_projects(U); t = tasks(); t = t[t.project_id.isin(ids)]
    A = "#1E4E8C"
    a, b = st.columns(2, gap="large")
    with a:
        sec("Project performance", "Progress by project")
        st.bar_chart(PROJ.loc[ids][["name", "progress"]].set_index("name"), color=A, height=260)
        sec("Task completion", "Tasks by state per project")
        st.bar_chart(t.assign(project=t.project_id.map(pname)).pivot_table(index="project", columns="state", values="id", aggfunc="count", fill_value=0), height=260)
        sec("Issue trends", "Issues by priority")
        i = D["issues"]; i = i[i.project_id.isin(ids)]
        if len(i): st.bar_chart(i.groupby("priority").size(), color=A, height=220)
        else: empty("No issues recorded", "Issue counts will appear here.")
    with b:
        sec("Department activity", "Recorded actions by department")
        ac = D["activities"]
        if len(ac): st.bar_chart(ac.groupby(ac.actor_id.map(lambda x: dn(EMP.dept_id.get(x)))).size(), color=A, height=260)
        else: empty("No activity yet", "Activity counts will appear here.")
        sec("Document activity", "Documents by category")
        d = visible_docs(U)
        if len(d): st.bar_chart(d.groupby("category").size(), color=A, height=260)
        else: empty("No documents yet", "Document counts will appear here.")
        sec("Open task workload", "Per employee")
        o = t[t.status != "Completed"]
        if len(o): st.bar_chart(o.groupby(o.assignee_id.map(ename)).size(), color=A, height=220)
        else: empty("No open tasks", "Workload will appear here.")
    sec("Budget spent against budget")
    st.bar_chart(PROJ.loc[ids][["name", "budget", "spent"]].set_index("name"), height=260)

def enterprise_health():
    top("Insights", "Enterprise Health")
    head("Enterprise Health", "Status is calculated from project, task and issue data using the rules shown below.")
    ids = my_projects(U); hs = {i: health(i) for i in ids}; t = tasks(); t = t[t.project_id.isin(ids)]
    iss = D["issues"]; iss = iss[iss.project_id.isin(ids) & (iss.priority == "Critical") & (iss.status == "Open")]
    overall = "Critical" if "Critical" in hs.values() else ("At Risk" if "At Risk" in hs.values() else "On Track")
    kv([("Overall", badge(overall)), ("Rule", "Worst status of any active project")])
    od = int((t.state == "Overdue").sum())
    kpis([("On Track", sum(v == "On Track" for v in hs.values()), False), ("At Risk", sum(v == "At Risk" for v in hs.values()), False),
          ("Critical", sum(v == "Critical" for v in hs.values()), any(v == "Critical" for v in hs.values())), ("Overdue tasks", od, od > 0), ("Critical issues", len(iss), len(iss) > 0)])
    sec("Needs attention")
    items = [li(PROJ.name[i], [f"due {fd(PROJ.deadline[i])}", "Project"], badge(h)) for i, h in hs.items() if h in ("At Risk", "Critical")]
    items += [li(r.title, [f"overdue since {fd(r.due)}", pn(r.project_id), ename(r.assignee_id)], badge("Overdue")) for _, r in t[t.state == "Overdue"].iterrows()]
    items += [li(r.title, [pn(r.project_id), "Critical issue"], badge("Critical")) for _, r in iss.iterrows()]
    listbox(items, "Nothing needs attention", "All projects are on track with no overdue work.")
    sec("Document availability")
    dd = D["documents"]
    listbox([li(PROJ.name[i], [f"{int((dd.project_id == i).sum())} linked documents"]) for i in ids], "No projects", "")
    st.caption("Rules: Critical if 3 or more tasks are overdue or a critical issue is open. At Risk if any task is overdue, or the deadline is within 14 days and progress is under 80%.")

def answer(q):
    P, tk, dc, em, iss = search(q, U); ql = q.lower(); src = []
    named = [i for i in P]
    out = ""
    if named and any(w in ql for w in ["status", "progress", "how is", "problem", "issue"]):
        for i in named:
            t = tasks(); t = t[t.project_id == i]; od = t[t.state == "Overdue"]
            out += f"**{PROJ.name[i]}** is {PROJ.progress[i]}% complete and rated **{health(i)}**. Manager: {ename(PROJ.manager_id[i])}. Deadline: {PROJ.deadline[i]}. {len(od)} overdue task(s), {int((D['issues'][D['issues'].project_id==i].status=='Open').sum())} open issue(s).\n\n"
            for _, r in iss[iss.project_id == i].iterrows(): out += f"- Issue: {r.title} ({r.priority})\n"
            src += [f"{PROJ.name[i]} project record", "Task database"]
    elif "overdue" in ql:
        out = "Overdue tasks:\n\n" + "".join(f"- {r.title} ({pname(r.project_id)}, {ename(r.assignee_id)}, due {r.due})\n" for _, r in tk.iterrows()) if len(tk) else "There are no overdue tasks."
        src = ["Task database"]
    elif named and ("who" in ql or "working" in ql):
        m = D["project_members"]
        for i in named: out += f"**{PROJ.name[i]}** team: " + ", ".join(EMP.name[e] for e in m[m.project_id == i].employee_id) + "\n\n"
        src = ["Project members"]
    elif "who" in ql and em:
        out = "Matching people: " + ", ".join(f"{EMP.name[i]} ({EMP.designation[i]})" for i in em); src = ["Employee directory"]
    elif len(dc):
        r = dc.sort_values("created", ascending=False).iloc[0]
        out = f"The most relevant document is **{r['name']}** ({r.version}, uploaded {r.created} by {ename(r.uploader_id)}). {r.description}"
        src = [r["name"]]
    if not out:
        return "I could not find this in the records available to you. Try a project, person, or document name."
    return out + "\n\n**Sources:** " + ", ".join(dict.fromkeys(src))

def _ask(q):
    st.session_state.chat.append({"r": "user", "t": q})
    st.session_state.chat.append({"r": "assistant", "t": answer(q)})

def assistant():
    top("AI", "AI Assistant")
    head("AI Assistant", "Answers come only from EnterprisePulse records you can access, with sources shown.")
    if "chat" not in st.session_state: st.session_state.chat = []
    if not st.session_state.chat:
        sec("Suggested questions")
        for s in ["What is the status of Project Alpha?", "Which tasks are overdue?", "Show documents related to billing.", "Who is working on Project Beta?"]:
            if st.button(s, key=f"sg:{s}", icon=":material/arrow_forward:", type="tertiary"):
                _ask(s); st.rerun()
    for k, m in enumerate(st.session_state.chat):
        with st.chat_message(m["r"]):
            if m["r"] == "assistant" and "\n\n**Sources:** " in m["t"]:
                body, srcs = m["t"].split("\n\n**Sources:** ", 1)
                st.markdown(body)
                md(f"<div class='src'><b>Sources</b>{esc(srcs)}</div>")
                P, tk, dc, em, iss = search(st.session_state.chat[k - 1]["t"], U)
                rel = [PROJ.name[i] for i in P][:3] + (list(dc["name"])[:3] if len(dc) else [])
                if rel:
                    md("<div class='src'><b>Related records</b>" + "".join(f"<span class='tag'>{esc(x)}</span>" for x in rel) + "</div>")
            else:
                st.markdown(m["t"])
    q = st.chat_input("Ask about a project, task, person or document")
    if q:
        _ask(q); st.rerun()

# ======================================================================
# Navigation shell
# ======================================================================
PG = {
    "Dashboard": st.Page(dashboard, title="Dashboard", icon=":material/dashboard:", url_path="dashboard", default=True),
    "Search": st.Page(search_page, title="Search", icon=":material/search:", url_path="search"),
    "Knowledge Base": st.Page(kb, title="Knowledge Base", icon=":material/menu_book:", url_path="knowledge-base"),
    "Documents": st.Page(documents, title="Documents", icon=":material/description:", url_path="documents"),
    "Policies": st.Page(policies, title="Policies", icon=":material/policy:", url_path="policies"),
    "Reports": st.Page(reports, title="Reports", icon=":material/summarize:", url_path="reports"),
    "Projects": st.Page(projects, title="Projects", icon=":material/folder_open:", url_path="projects"),
    "Tasks": st.Page(tasks_page, title="Tasks", icon=":material/task_alt:", url_path="tasks"),
    "Issues": st.Page(issues_page, title="Issues", icon=":material/error_outline:", url_path="issues"),
    "Employees": st.Page(employees, title="Employees", icon=":material/group:", url_path="employees"),
    "Departments": st.Page(departments, title="Departments", icon=":material/account_tree:", url_path="departments"),
    "Notifications": st.Page(notifications, title="Notifications", icon=":material/notifications:", url_path="notifications"),
    "Activity": st.Page(activity, title="Activity", icon=":material/history:", url_path="activity"),
    "AI Assistant": st.Page(assistant, title="AI Assistant", icon=":material/chat:", url_path="ai-assistant"),
}
if U.role in ("manager", "admin"):
    PG["Analytics"] = st.Page(analytics, title="Analytics", icon=":material/bar_chart:", url_path="analytics")
    PG["Enterprise Health"] = st.Page(enterprise_health, title="Enterprise Health", icon=":material/monitor_heart:", url_path="enterprise-health")
if U.role == "admin":
    PG["Audit Log"] = st.Page(lambda: activity(True), title="Audit Log", icon=":material/fact_check:", url_path="audit-log")

SECTIONS = {"Home": ["Dashboard", "Search"], "Knowledge": ["Knowledge Base", "Documents", "Policies", "Reports"],
            "Work": ["Projects", "Tasks", "Issues"], "People": ["Employees", "Departments"],
            "Insights": ["Analytics", "Enterprise Health"], "Communication": ["Notifications", "Activity", "Audit Log"], "AI": ["AI Assistant"]}
NAV = {s: [PG[n] for n in names if n in PG] for s, names in SECTIONS.items()}
NAV = {s: v for s, v in NAV.items() if v}

try:
    st.logo("assets/logo.svg", icon_image="assets/icon.svg", size="large")
except Exception:
    pass
page = st.navigation(NAV, position="sidebar")
with st.sidebar:
    md(f"<div style='display:flex;gap:.6rem;align-items:center'><div class='av' aria-hidden='true'>{esc(initials(U['name']))}</div>"
       f"<div><div style='font-weight:600;font-size:14px'>{esc(U['name'])}</div><div class='crumb'>{esc(U.role.title())} · {esc(dn(U.dept_id))}</div></div></div>")
    if st.button("Sign out", icon=":material/logout:", type="tertiary"):
        sb.auth.sign_out(); st.session_state.clear(); st.rerun()
import streamlit.components.v1 as components
components.html("""<script>
const d = window.parent.document;
if (!d.__epk) { d.__epk = true;
  d.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      const i = d.querySelector('input[aria-label="Global search"]');
      if (i) { e.preventDefault(); i.focus(); i.select(); }
    }
  });
}
</script>""", height=0)
page.run()
