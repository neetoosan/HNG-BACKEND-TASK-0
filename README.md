# HNG Stage 0 Gender Classifier API

FastAPI backend for the HNG Stage 0 API Integration and Data Processing assessment.

The API exposes:

```text
GET /api/classify?name=<name>
```

It calls the Genderize API, processes the response, and returns the required assignment response format.

## Features

- `GET /api/classify` endpoint.
- Validates missing or empty `name` with `400 Bad Request`.
- Handles repeated `name` query parameters with `422 Unprocessable Entity`.
- Calls `https://api.genderize.io`.
- Extracts `gender`, `probability`, and `count`.
- Renames `count` to `sample_size`.
- Computes `is_confident` only when `probability >= 0.7` and `sample_size >= 100`.
- Generates fresh UTC `processed_at` timestamps.
- Returns all errors as `{ "status": "error", "message": "..." }`.
- Adds `Access-Control-Allow-Origin: *` to every response.
- Includes a Vercel entrypoint at `app/index.py`.

## Setup

```bash
git clone <repo-url>
cd HNG-14-BACKEND
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For macOS/Linux:

```bash
source venv/bin/activate
```

## Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test in the browser:

```text
http://localhost:8000/api/classify?name=john
```

## Success Response

```json
{
  "status": "success",
  "data": {
    "name": "john",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 509298,
    "is_confident": true,
    "processed_at": "2026-04-16T12:00:00Z"
  }
}
```

## Error Response

```json
{
  "status": "error",
  "message": "Missing or empty 'name' query parameter"
}
```

## Tests

```bash
python -m pytest tests -v
```

## Deploy To Vercel

This repository includes `app/index.py`, which Vercel uses as the FastAPI entrypoint.

Recommended Vercel settings:

```text
Framework Preset: Other
Build Command: leave empty
Output Directory: leave empty
Install Command: pip install -r requirements.txt
```

If you have a Genderize API key, add this environment variable in Vercel:

```text
GENDERIZE_API_KEY=<your-genderize-api-key>
```

After deployment, test:

```text
https://your-vercel-domain.vercel.app/api/classify?name=john
```

For submission, provide the public base URL only:

```text
https://your-vercel-domain.vercel.app
```

## Submission

- GitHub repository link: `<your-github-repo-url>`
- Public API base URL: `<your-public-api-base-url>`
