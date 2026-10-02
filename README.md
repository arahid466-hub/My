# Aether Complete

Self-owned Aether control-plane with local-first adapters, authenticated GPU-worker boundary, model manifest, hardware detection, job APIs, Web UI and configurable Android WebView client.

## Honest runtime behavior
No media is synthesized by a placeholder. Chat uses local Ollama when configured. TTS uses Piper with a verified local voice model. Image/video require a real ComfyUI/diffusion/video adapter and suitable GPU; if unavailable the job fails clearly. Railway is the API/control-plane and should forward heavy jobs to a separate GPU worker.

## Start
```bash
cp .env.example .env
./scripts/install_aether.sh
./aether start
```
Or:
```bash
docker compose up --build
# after startup: docker compose exec ollama ollama pull llama3.2
```

## Railway
Deploy the root Dockerfile, add a persistent volume at `/data/aether`, set secrets from `.env.example`, and configure a separate GPU host running the worker with a strong `AETHER_WORKER_TOKEN`. Railway provides `PORT` automatically.

## Models
`models/manifest.json` is the license-aware catalog. Large weights are not bundled. Use `scripts/install_model.py SOURCE DEST --sha256 CHECKSUM`; a mismatch refuses installation. Review upstream licenses before downloading.

At boot, `scripts/model_manager.py` automatically installs only entries that contain both an explicit `download_url` and an exact SHA256 in the manifest. Entries without both fields are deliberately not downloaded and remain `UNAVAILABLE`; this prevents an unverified model from being reported as READY. Corrupt files are quarantined and repaired only from a verified source. The deployment report is written to `/data/aether/deployment-report.json` and is exposed at `/api/deployment-report`.

## Android
Open `android/` in Android Studio, build the APK, then use the menu to set the Aether server URL. Heavy models never live in the APK.

## Security
Do not expose the default local admin password publicly. Use HTTPS, long worker tokens, a private worker network, authenticated file routes, and a production password/session store before public multi-user use. The worker rejects unauthenticated calls and refuses GPU-only media work without CUDA.
