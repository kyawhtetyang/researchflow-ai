# ResearchFlow AI Frontend

React + Vite frontend for the ResearchFlow AI design prototype.

## Purpose
- Use the RAG Knowledge Assistant chat-first layout as the baseline.
- Refactor the copied UI into a ResearchFlow-specific research assistant.
- Connect the approved chat UI to the async ResearchFlow backend contract.
- Current source uses job creation plus polling: `POST /api/research/` and `GET /api/research/{job_id}/chat`.

## Local Run
```bash
npm install
npm run dev
```

The Vite dev server uses port `3001` by default. If that port is busy, use the URL printed by Vite.

## Build
```bash
npm run build
```

Future Vercel settings should use:
- root directory: `frontend/`
- build command: `npm run build`
- output directory: `dist`

## Current Integration Rule
- Keep the UI chat-first.
- Use `/api/research/{job_id}/chat` as the primary frontend contract.
- Keep workflow and sources as optional supporting details below the answer.
