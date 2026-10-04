# Put PA Desk online, with data that survives restarts

The app keeps its cases, users and sign-ins in one SQLite file. On a host with a **persistent disk**, a restart or a new deploy keeps all of it.

## What you need
- A GitHub repo with this code (already there).
- A Render account (render.com). The plan that supports a disk is **Starter, about $7 a month, plus about $0.25 a month for 1 GB of disk**. You can delete the service after the interview.
- Your three keys, entered in Render's dashboard and never in chat or in the repo: `ANTHROPIC_API_KEY`, `UNSTRUCTURED_API_KEY`, `HONEYCOMB_API_KEY`.

## Steps (about 15 minutes)
1. Push the latest code to GitHub.
2. In Render: **New > Blueprint**, pick this repo. It reads `render.yaml`, which sets up the web service, the 1 GB disk at `/data`, and the other settings.
3. Fill in the three secret values when Render asks. If you skip `HONEYCOMB_API_KEY` the app runs with no telemetry. If you skip `UNSTRUCTURED_API_KEY` scanned packets fall back to the local reader.
4. Click create. The first build takes a few minutes. When it says Live, open the URL. Sign in with a demo account (password `demo1234`).
5. Set an **Anthropic monthly spend limit** in the Anthropic console (Plans & Billing, for example $20), so a shared link can never run up a bill.

## Check it kept your data
Upload a packet, then in Render choose **Manual Deploy > Restart**. After it restarts, reload: you stay signed in and the case is still there.

## Guards already in the app
- Only PDFs, up to 15 MB each.
- At most 40 new packets a day (`PA_MAX_UPLOADS_PER_DAY`). Past that, the app says to try tomorrow.
- Sign-in cookies are secure and last 14 days.
- Everything on the screen is made-up data. The footer of each test packet says so.

## Before the interview
- **Reset to a clean demo, once:** sign in as intake (Carla), then run
  `curl -X POST https://YOUR-URL/api/admin/reset-demo -H "Content-Type: application/json" -H "Cookie: sid=YOUR_SESSION" -d "{\"confirm\":\"RESET\"}"`
  or ask me to do it with you. It wipes every case and re-seeds the demo data, and it signs everyone out. Do this the day before, because the seeded cases age: their deadlines are counted from the day they were created.
- Do not reset after that. Normal restarts and deploys keep everything.
- Open `YOUR-URL/ops.html` while signed in as intake or a medical director to show the live dashboard.

## What is not on the host
The Honeycomb board and the recall and precision evals run from your computer. The hosted app only sends its traces to the same Honeycomb board.

## Other hosts
The `Dockerfile` runs anywhere. On Fly.io or Railway, mount a volume at `/data` and set the same environment variables. Without a volume, a restart wipes the data.
