# EnterprisePulse

EnterprisePulse is a Streamlit + Supabase enterprise knowledge platform.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Create `.streamlit/secrets.toml` locally:

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

Run `schema.sql` in the Supabase SQL Editor and create a public Storage bucket named `documents`.

## Render

Render uses `render.yaml` and requires these environment variables:

- `SUPABASE_URL`
- `SUPABASE_KEY`

The app starts with:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

## Dependency note

Pandas is pinned to `2.3.3` because that is the working version used by the Sales Data Mining project and is compatible with the current EnterprisePulse code.
