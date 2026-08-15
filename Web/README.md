# Forest AI Vision Web

Vue 3 + Vite frontend for the local YOLO vision API in `AI/api_server.py`.
It supports image upload detection and browser camera snapshot detection.

## Features

- Upload an image and show boxes, labels, counts, and confidence scores.
- Open the browser camera, capture the current frame, and run detection.
- Open the saved detection result image.

## Development

Start the vision API from the project root:

```powershell
.\.venv\Scripts\python.exe .\AI\api_server.py
```

Then start the web app from the `Web` directory:

```powershell
pnpm install
pnpm dev
```

Visit `http://127.0.0.1:5173` for development mode. For daily demo usage,
start the vision API and visit `http://127.0.0.1:8000`.

## Production Build

```powershell
pnpm build
```

The build output is written to `dist/` and can be served directly by
`AI/api_server.py`.

If the frontend and backend use different addresses, set `VITE_API_BASE_URL`
before building:

```powershell
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
pnpm build
```
