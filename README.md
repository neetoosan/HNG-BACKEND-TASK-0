# HNG Stage 0 - Gender Classifier API

A FastAPI backend that exposes `GET /api/classify`, calls the Genderize API, and returns a processed gender prediction response.

## Setup

```bash
git clone <repo-url>
cd HNG-14-BACKEND
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For macOS/Linux activation, use:

```bash
source venv/bin/activate
```

## Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Endpoint

`GET /api/classify?name=<name>`

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Yes | Name to classify |

## Example Request

```bash
curl "http://localhost:8000/api/classify?name=james"
```

## Success Response

```json
{
  "status": "success",
  "data": {
    "name": "james",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-16T08:00:00Z"
  }
}
```

## Error Response

```json
{
  "status": "error",
  "message": "<error description>"
}
```

| Status Code | Condition |
| --- | --- |
| `400` | Missing or empty `name` parameter |
| `400` | No prediction available for the provided name |
| `422` | Invalid input |
| `502` | Genderize API is unreachable or returns an invalid response |
| `500` | Unexpected server error |

## Confidence Logic

`is_confident` is `true` only when both conditions are met:

```text
probability >= 0.7
sample_size >= 100
```

## Run Tests

```bash
python -m pytest tests -v
```

## Project Structure

```text
app/
  main.py
  routes/classify.py
  schemas/responses.py
  services/genderize.py
  utils/errors.py
tests/
  test_classify.py
requirements.txt
README.md
```

## Submission

- GitHub repository link: `<your-github-repo-url>`
- Public API base URL: `<your-deployed-api-url>`
