# Deployment

## Railway backend

Deploy the `backend/` directory as the Railway service root. Attach a persistent volume at `/data`, then set:

```text
DATABASE_URL=sqlite:////data/fireflies.db
UPLOAD_DIR=/data/uploads
CORS_ORIGINS=["https://YOUR-VERCEL-PROJECT.vercel.app"]
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

`railway.toml` runs `alembic upgrade head` before Uvicorn. Do not use temporary storage for SQLite or recordings.

## Vercel frontend

Deploy the `frontend/` directory as the Vercel project root and set:

```text
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-SERVICE.up.railway.app
```

Then add the actual Vercel origin to Railway `CORS_ORIGINS` and verify `/health`, the library, and a transcript upload.
