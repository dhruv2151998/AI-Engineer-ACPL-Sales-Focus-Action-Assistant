# F1 Capstone Template

Starter repository for the Cadra F1 walking-skeleton capstone. Use OpenCode with the Cadra provider to build your solution, document your approach, and submit a public GitHub repo for evaluation.

## Prerequisites

- Python 3.11+
- [OpenCode](https://opencode.ai) ≥ 1.17.0
- A Cadra JWT (`CADRA_TOKEN`) from the F1 Setup page
- Your Cadra proxy URL (from the F1 Setup page)

## Setup

1. Clone this repo (or use it as a GitHub template).
2. Set the environment variables (both values come from the F1 Setup page):
   ```bash
   export CADRA_PROXY_URL='https://github.com/varunharsha1992/cadra-base-template'  # e.g. https://your-proxy.example.com/v1
   export CADRA_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTI2ZDA5Ny00MTRlLTRlNGQtODU5ZS05NGE1YzUxMTY2NDgiLCJ1c2VyX2lkIjoiOGEyNmQwOTctNDE0ZS00ZTRkLTg1OWUtOTRhNWM1MTE2NjQ4IiwiY29kaW5nX2Fzc2Vzc21lbnRfaWQiOiJhMjdhOGMyYS0zNjk4LTRlY2UtODZhMC02NTdhMDE1ODVmNjciLCJ0eXBlIjoiZjEtY29kaW5nIiwiZW52aXJvbm1lbnQiOiJtYW5hZ2VkIiwicHVycG9zZSI6ImFnZW50IiwiaWF0IjoxNzg5Mjc2OTQ5LCJleHAiOjE3ODk3MDg5NDl9.EhtJR6dn0Ee3nRJQ46TQfIqRZQKRPQh38Qe3fuF_YhE'
   ```
   `opencode.json` reads both via `{env:…}` — no file edits needed.
3. Install OpenCode if not already installed (see [opencode.ai](https://opencode.ai)).
4. Run OpenCode in this directory:
   ```bash
   opencode
   ```
5. Complete `APPROACH.md` and implement your solution in `src/` (start with `src/solution.py`).
6. Push your work to a **public** GitHub repository.
7. Submit your repo URL on the F1 demo page.

## Python environment (optional)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Project layout

```
.
├── opencode.json    # Cadra provider config (reads CADRA_PROXY_URL + CADRA_TOKEN from env)
├── APPROACH.md      # Your written approach (required for submission)
├── src/
│   └── solution.py  # Your solution code
├── requirements.txt
└── README.md
```
