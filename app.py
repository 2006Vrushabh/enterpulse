import os
import re
from datetime import date
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="EnterprisePulse", layout="wide", initial_sidebar_state="expanded")

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

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
:root{--ink:#17212B;--mute:#5F6B78;--line:#E1E5EA;--bg:#F5F6F8;--acc:#0B6E6E}
html,body,[class*="css"],.stApp{font-family:'IBM Plex Sans',sans-serif;color:var(--ink)}
.stApp{background:var(--bg)} #MainMenu,footer,header{visibility:hidden}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line);min-width:240px}
h1{font-size:1.5rem!important;font-weight:600!important;letter-spacing:-.01em} h2,h3{font-weight:600!important}
.stButton>button,.stDownloadButton>button{border-radius:6px;border:1px solid var(--line);font-weight:500;background:#fff;color:var(--ink)}
.stButton>button[kind="primary"]{background:var(--acc);border-color:var(--acc);color:#fff}
.stButton>button:hover{border-color:var(--acc);color:var(--acc)} .stButton>button[kind="primary"]:hover{color:#fff;filter:brightness(1.1)}
div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:6px;padding:12px 14px}
div[data-testid="stMetricLabel"]{color:var(--mute)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px}
.row{background:#fff;border:1px solid var(--line);border-radius:6px;padding:10px 14px;margin-bottom:6px}
.row b{font-weight:600}.meta{color:var(--mute);font-size:.86rem}
.lbl{color:var(--mute);font-size:.86rem;font-weight:500;margin:18px 0 6px}
</style>""", unsafe_allow_html=True)

TABLES = ["departments","employees","projects","project_members","tasks","documents",
          "document_versions","issues","activities","notifications"]

@st.cache_data(ttl=15)
def load():
    return {t: pd.DataFrame(sb.table(t).select("*").execute().data) for t in TABLES}

def refresh():
    load.clear()

D = load()
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

def dot(s):
    return f"<span class='dot' style='background:{COL.get(s,'#8A94A0')}'></span>{s}"

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

# ---------- auth ----------
def login():
    _, c, _ = st.columns([1, 1.1, 1])
    with c:
        st.write(""); st.write("")
        st.markdown("### EnterprisePulse")
        st.caption("Enterprise Knowledge Warehouse")
        email = st.text_input("Employee ID or email")
        pw = st.text_input("Password", type="password")
        if st.button("Sign in", type="primary", use_container_width=True):
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

PAGES = ["Dashboard", "Search", "Knowledge Base", "Documents", "Projects", "Employees", "Notifications", "AI Assistant"]
if U.role in ("manager", "admin"):
    PAGES += ["Analytics", "Enterprise Health"]
if U.role == "admin":
    PAGES += ["Audit Log"]
with st.sidebar:
    st.markdown("**EnterprisePulse**")
    st.caption(f"{U['name']}, {U.role.title()}")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    if st.button("Sign out"):
        sb.auth.sign_out(); st.session_state.clear(); st.rerun()

def row(title, meta):
    st.markdown(f"<div class='row'><b>{title}</b><div class='meta'>{meta}</div></div>", unsafe_allow_html=True)

def doc_row(r):
    row(r["name"], f"{r.category} · {DEPT.get(r.dept_id,'')} · {ename(r.uploader_id)} · {r.created} · {r.version} · {r.access}")

# ---------- pages ----------
def dashboard():
    st.title(f"{'Good morning' if pd.Timestamp.now().hour < 12 else 'Good afternoon'}, {U['name'].split()[0]}")
    ids = my_projects(U); t = tasks()
    mt = t[(t.assignee_id == U.id) & (t.status != "Completed")]
    c = st.columns(5)
    c[0].metric("Projects", len(ids)); c[1].metric("Active tasks", len(mt))
    c[2].metric("Documents", len(visible_docs(U)))
    c[3].metric("Notifications", len(D["notifications"][D["notifications"].employee_id.isin([U.id]) | D["notifications"].employee_id.isna()]))
    c[4].metric("Pending actions", int((mt.state == "Overdue").sum()))
    a, b = st.columns(2)
    with a:
        st.markdown("<div class='lbl'>Project health</div>", unsafe_allow_html=True)
        for pid in ids:
            row(PROJ.name[pid], f"{dot(health(pid))} · {PROJ.progress[pid]}% complete")
        st.markdown("<div class='lbl'>Upcoming deadlines</div>", unsafe_allow_html=True)
        up = t[(t.status != "Completed") & (t.project_id.isin(ids))].sort_values("due").head(5)
        for _, r in up.iterrows():
            row(r.title, f"{pname(r.project_id)} · due {r.due} · {r.state}")
    with b:
        st.markdown("<div class='lbl'>Recent activity</div>", unsafe_allow_html=True)
        act = D["activities"].sort_values("at", ascending=False).head(6)
        for _, r in act.iterrows():
            row(f"{ename(r.actor_id)} {r.action}", str(r.at)[:10])
        st.markdown("<div class='lbl'>Recently added documents</div>", unsafe_allow_html=True)
        for _, r in visible_docs(U).sort_values("created", ascending=False).head(3).iterrows():
            doc_row(r)

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
    st.title("Search")
    q = st.text_input("Search", placeholder="Search anything in EnterprisePulse...", label_visibility="collapsed")
    if not q:
        st.caption("Try: Project Alpha, leave policy, Python, overdue tasks")
        return
    P, tk, dc, em, iss = search(q, U)
    if not (P or len(tk) or len(dc) or em or len(iss)):
        st.info("No results. Check the spelling or search by project, person or document name.")
    if P:
        st.markdown("<div class='lbl'>Projects</div>", unsafe_allow_html=True)
        for i in P:
            row(PROJ.name[i], f"{PROJ.progress[i]}% complete · Manager: {ename(PROJ.manager_id[i])} · {dot(health(i))}")
    if len(dc):
        st.markdown("<div class='lbl'>Documents and reports</div>", unsafe_allow_html=True)
        for _, r in dc.iterrows(): doc_row(r)
    if em:
        st.markdown("<div class='lbl'>Employees</div>", unsafe_allow_html=True)
        for i in em: row(EMP.name[i], f"{EMP.designation[i]} · {DEPT.get(EMP.dept_id[i])}")
    if len(tk):
        st.markdown("<div class='lbl'>Tasks</div>", unsafe_allow_html=True)
        for _, r in tk.iterrows(): row(r.title, f"{pname(r.project_id)} · {ename(r.assignee_id)} · due {r.due} · {r.state}")
    if len(iss):
        st.markdown("<div class='lbl'>Issues</div>", unsafe_allow_html=True)
        for _, r in iss.iterrows(): row(r.title, f"{pname(r.project_id)} · {r.priority} · {r.status}")

def kb():
    st.title("Knowledge Base")
    d = visible_docs(U)
    for cat in ["Policies", "SOPs", "Guidelines", "Reports", "Technical", "Financial", "Meeting Minutes"]:
        sub = d[d.category == cat] if len(d) else d
        with st.expander(f"{cat} ({len(sub)})"):
            if sub.empty: st.caption("No documents in this category yet.")
            for _, r in sub.iterrows(): doc_row(r)

def documents():
    st.title("Documents")
    d = visible_docs(U)
    c = st.columns([2, 1, 1, 1])
    q = c[0].text_input("Filter", placeholder="Filter by name or description", label_visibility="collapsed")
    cat = c[1].selectbox("Category", ["All"] + sorted(d.category.unique()) if len(d) else ["All"], label_visibility="collapsed")
    dep = c[2].selectbox("Department", ["All"] + sorted(DEPT.values()), label_visibility="collapsed")
    srt = c[3].selectbox("Sort", ["Newest", "Name"], label_visibility="collapsed")
    if q:
        name_match = d["name"].fillna("").str.contains(q, case=False, na=False)
        desc_match = d["description"].fillna("").str.contains(q, case=False, na=False)
        d = d[name_match | desc_match]
    if cat != "All": d = d[d.category == cat]
    if dep != "All": d = d[d.dept_id.map(DEPT) == dep]
    d = d.sort_values("created", ascending=False) if srt == "Newest" else d.sort_values("name")
    left, right = st.columns([3, 2])
    with left:
        if d.empty: st.info("No documents match these filters.")
        for _, r in d.iterrows():
            doc_row(r)
            with st.expander("Details and version history"):
                st.write(r.description)
                st.caption(f"Project: {pname(r.project_id)} · Latest version: {r.version}")
                v = D["document_versions"]; v = v[v.document_id == r["id"]].sort_values("created", ascending=False)
                for _, x in v.iterrows():
                    st.write(f"{x.version}{' (latest)' if x.version == r.version else ''}: {x.note}, {x.created}")
                if r.path:
                    st.link_button("Download", sb.storage.from_("documents").get_public_url(r.path))
    with right:
        st.markdown("##### Upload a document")
        f = st.file_uploader("File")
        name = st.text_input("Document name", value=f.name if f else "")
        cat = st.selectbox("Category ", ["Policies", "SOPs", "Guidelines", "Reports", "Technical", "Financial", "Meeting Minutes"])
        dep = st.selectbox("Department ", list(DEPT.values()), index=int(U.dept_id) - 1)
        pr = st.selectbox("Project", ["None"] + [PROJ.name[i] for i in my_projects(U)])
        desc = st.text_area("Description")
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
                st.success("Document uploaded."); st.rerun()

def projects():
    st.title("Projects")
    ids = my_projects(U)
    if not ids: st.info("You are not on any projects yet."); return
    for i in ids:
        row(PROJ.name[i], f"{dot(health(i))} · {PROJ.progress[i]}% · Manager: {ename(PROJ.manager_id[i])} · due {PROJ.deadline[i]}")
    pid = st.selectbox("Open project", ids, format_func=lambda i: PROJ.name[i])
    p = PROJ.loc[pid]; t = tasks(); t = t[t.project_id == pid]
    iss = D["issues"]; iss = iss[iss.project_id == pid]
    st.subheader(p["name"]); st.markdown(f"Manager: {ename(p.manager_id)} · {dot(health(pid))}", unsafe_allow_html=True)
    c = st.columns(6)
    c[0].metric("Progress", f"{p.progress}%"); c[1].metric("Deadline", str(p.deadline)[5:])
    c[2].metric("Budget used", f"{int(p.spent/p.budget*100)}%"); c[3].metric("Tasks", len(t))
    c[4].metric("Overdue", int((t.state == "Overdue").sum())); c[5].metric("Open issues", int((iss.status == "Open").sum()))
    tabs = st.tabs(["Overview", "Tasks", "Team", "Documents", "Issues", "Activity"])
    with tabs[0]:
        st.progress(int(p.progress) / 100)
        st.caption("Status rules: Critical if 3 or more tasks are overdue or a critical issue is open. At Risk if any task is overdue, or the deadline is within 14 days and progress is under 80%.")
    with tabs[1]:
        for _, r in t.sort_values("due").iterrows():
            row(r.title, f"{ename(r.assignee_id)} · due {r.due} · {r.priority} · {r.state}")
        if U.role in ("manager", "admin"):
            a, b, c2 = st.columns([3, 2, 1])
            tid = a.selectbox("Task", t["id"], format_func=lambda i: t[t["id"] == i].title.iloc[0])
            ns = b.selectbox("Status", ["To Do", "In Progress", "Blocked", "Completed"])
            if c2.button("Update task"):
                sb.table("tasks").update({"status": ns}).eq("id", int(tid)).execute()
                log(U, f"updated a task to {ns} on {p['name']}", int(pid), None, notify=True); st.rerun()
    with tabs[2]:
        m = D["project_members"]; m = m[m.project_id == pid].employee_id
        for e in m:
            n = t[t.assignee_id == e]
            row(EMP.name[e], f"{EMP.designation[e]} · {len(n)} tasks on this project")
    with tabs[3]:
        d = visible_docs(U); d = d[d.project_id == pid] if len(d) else d
        if d.empty: st.caption("No documents linked to this project.")
        for _, r in d.iterrows(): doc_row(r)
    with tabs[4]:
        if iss.empty: st.caption("No issues recorded.")
        for _, r in iss.iterrows(): row(r.title, f"{r.priority} · Owner: {ename(r.owner_id)} · {r.status} · {r.created}")
    with tabs[5]:
        a = D["activities"]; a = a[a.project_id == pid].sort_values("at", ascending=False)
        for _, r in a.iterrows(): row(f"{ename(r.actor_id)} {r.action}", str(r.at)[:16])

def employees():
    st.title("Employees")
    q = st.text_input("Search employees", placeholder="Name, department, role, skill or project", label_visibility="collapsed")
    mem = D["project_members"]
    for i in EMP.index:
        prj = [PROJ.name[x] for x in mem[mem.employee_id == i].project_id]
        blob = f"{EMP.name[i]} {DEPT.get(EMP.dept_id[i])} {EMP.designation[i]} {' '.join(EMP.skills[i] or [])} {' '.join(prj)}".lower()
        if q.lower() in blob:
            row(EMP.name[i], f"{EMP.designation[i]} · {DEPT.get(EMP.dept_id[i])} · Skills: {', '.join(EMP.skills[i] or [])} · Projects: {', '.join(prj) or 'None'}")

def notifications():
    st.title("Notifications")
    n = D["notifications"]; n = n[n.employee_id.isna() | (n.employee_id == U.id)].sort_values("created", ascending=False)
    if n.empty: st.info("You are all caught up.")
    for _, r in n.iterrows():
        row(r.text, f"{pname(r.project_id)} · {str(r.created)[:10]}")

def analytics():
    st.title("Analytics")
    ids = my_projects(U); t = tasks(); t = t[t.project_id.isin(ids)]
    st.markdown("<div class='lbl'>Tasks by state per project</div>", unsafe_allow_html=True)
    st.bar_chart(t.assign(project=t.project_id.map(pname)).pivot_table(index="project", columns="state", values="id", aggfunc="count", fill_value=0))
    st.markdown("<div class='lbl'>Open task workload per employee</div>", unsafe_allow_html=True)
    o = t[t.status != "Completed"]; st.bar_chart(o.groupby(o.assignee_id.map(ename)).size())
    st.markdown("<div class='lbl'>Budget spent against budget</div>", unsafe_allow_html=True)
    b = PROJ.loc[ids][["name", "budget", "spent"]].set_index("name"); st.bar_chart(b)

def enterprise_health():
    st.title("Enterprise Health")
    ids = my_projects(U); hs = {i: health(i) for i in ids}; t = tasks(); t = t[t.project_id.isin(ids)]
    iss = D["issues"]; iss = iss[iss.project_id.isin(ids) & (iss.priority == "Critical") & (iss.status == "Open")]
    c = st.columns(4)
    for k, col in zip(["On Track", "At Risk", "Critical"], c): col.metric(k, sum(v == k for v in hs.values()))
    c[3].metric("Overdue tasks", int((t.state == "Overdue").sum()))
    st.markdown("<div class='lbl'>Needs attention</div>", unsafe_allow_html=True)
    for i, h in hs.items():
        if h in ("At Risk", "Critical"): row(PROJ.name[i], f"{dot(h)} · due {PROJ.deadline[i]}")
    for _, r in t[t.state == "Overdue"].iterrows(): row(r.title, f"Overdue since {r.due} · {pname(r.project_id)} · {ename(r.assignee_id)}")
    for _, r in iss.iterrows(): row(r.title, f"Critical issue · {pname(r.project_id)}")
    st.markdown("<div class='lbl'>Document availability</div>", unsafe_allow_html=True)
    dd = D["documents"]
    for i in ids:
        row(PROJ.name[i], f"{int((dd.project_id == i).sum())} linked documents")

def assistant():
    st.title("AI Assistant")
    st.caption("Answers come only from EnterprisePulse records you can access, with sources shown.")
    if "chat" not in st.session_state: st.session_state.chat = []
    for m in st.session_state.chat:
        with st.chat_message(m["r"]): st.markdown(m["t"])
    q = st.chat_input("Ask about a project, task, person or document")
    if q:
        st.session_state.chat.append({"r": "user", "t": q})
        st.session_state.chat.append({"r": "assistant", "t": answer(q)}); st.rerun()

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

{"Dashboard": dashboard, "Search": search_page, "Knowledge Base": kb, "Documents": documents, "Projects": projects,
 "Employees": employees, "Notifications": notifications, "AI Assistant": assistant, "Analytics": analytics,
 "Enterprise Health": enterprise_health, "Audit Log": lambda: (st.title("Audit Log"), [row(f"{ename(r.actor_id)} {r.action}", f"{str(r.at)[:16]} · {pname(r.project_id)}") for _, r in D["activities"].sort_values("at", ascending=False).iterrows()])}[page]()
