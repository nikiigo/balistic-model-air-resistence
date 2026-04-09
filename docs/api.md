# API

This project exposes a small browser-facing HTTP API through the WSGI app in `ballistics/web/app.py`.

The main endpoint is `POST /api/simulate`. The browser normally reaches it only after loading `/` and completing the bootstrap flow.

## Browser Auth Flow

### `GET /`

Returns the main HTML page.

Behavior:
- If challenge mode is enabled and the browser does not yet have a valid session cookie, the page is rendered with `INITIAL_CSRF_TOKEN = ""` and a signed bootstrap challenge in `BOOTSTRAP_CHALLENGE`.
- If challenge mode is disabled, the server creates a signed browser session immediately, sets the session cookie, and renders a non-empty initial CSRF token into the page.
- If the browser already has a valid signed session cookie, the page is rendered with a CSRF token derived from that session.

Important details:
- The browser session cookie is signed and treated as opaque client state.
- Forged cookie values are ignored and do not produce a CSRF token.

### `POST /session/bootstrap`

Completes the browser bootstrap challenge and creates a browser session.

Request body:

```json
{
  "token": "signed-challenge-token",
  "answer": "user-answer"
}
```

Successful response:

```json
{
  "csrfToken": "session-derived-csrf-token"
}
```

On success the response also sets the signed browser session cookie.

Failure cases:
- `400 Bad Request` for invalid JSON, invalid token, or expired challenge
- `403 Forbidden` for disallowed origin or incorrect challenge answer

### CSRF Requirement For `POST /api/simulate`

Browser-session requests to `POST /api/simulate` must include:
- the signed session cookie
- `X-CSRF-Token` header matching the current session

Without a valid CSRF token, browser-session requests are rejected with `401 Unauthorized`.

An API key can also authorize the endpoint. When API-key auth is used, the CSRF header is not required.

## `POST /api/simulate`

Runs both the ideal and drag solvers and returns the plotted results and metrics.

### Authorization

The request must be authorized by one of:
- `X-API-Key` header matching the configured API key
- a valid signed browser session cookie plus `X-CSRF-Token`

If allowed origins are configured, the `Origin` header must also be in the allowlist.

### Required JSON Fields

The handler accepts a JSON object. In practice, the stable simulation contract requires these numeric fields:

```json
{
  "angle": 45.0,
  "speed": 55.0,
  "materialDensity": 1324.0,
  "temperature": 15.0,
  "pressure": 1.0,
  "diameter": 0.113,
  "dt": 0.016
}
```

Optional fields:
- `projectileShape`
- `sphericity`
- `volumeFactor`
- `dragModel`
- `ballisticCoefficient`
- `currentGun`

Notes:
- the payload must be a JSON object, not an array or scalar
- numeric fields are coerced to floats
- values are clamped to supported limits during normalization

### Sphere vs Shell Fields

#### Sphere / round shot

Use:

```json
{
  "projectileShape": "sphere"
}
```

Effective normalized behavior:
- `sphericity = 1.0`
- `volumeFactor = 1.0`
- `ballisticCoefficient = 0.0`
- `dragModel` is not the active physical driver for the sphere path

Sphere projectiles use the round-shot drag model, not the BC shell model.

#### Shell

Use:

```json
{
  "projectileShape": "shell",
  "sphericity": 0.68,
  "volumeFactor": 2.2,
  "dragModel": "g7",
  "ballisticCoefficient": 0.22
}
```

Notes:
- `dragModel` is normalized to `g1` or `g7`
- if `ballisticCoefficient` is omitted for shell payloads, the server falls back to the default shell BC
- shell responses report the effective BC used by the solver
- shell drag uses the same RK4 trajectory integrator as round shot, but with a different drag law
- the `g1`/`g7` shell drag law is velocity-banded in the current implementation; the table lookup is keyed by projectile speed converted to `ft/s`, then density-scaled for actual atmospheric conditions

### Key Response Structure

Successful response status:
- `200 OK`

Top-level shape:

```json
{
  "ideal": {
    "points": [],
    "metrics": {}
  },
  "drag": {
    "points": [],
    "metrics": {},
    "aero": {}
  },
  "focusedBounds": {
    "maxX": 0.0,
    "maxY": 0.0
  },
  "stableBounds": {
    "maxX": 0.0,
    "maxY": 0.0
  }
}
```

Important substructures:

- `ideal.points`
  - ideal analytical trajectory samples
- `ideal.metrics`
  - includes at least `range`, `maxHeight`, `flightTime`, and `peak`

- `drag.points`
  - per-step drag trajectory samples with aerodynamic data
  - each point includes:
    - `x`, `y`, `t`, `vx`, `vy`
    - `airDensity`, `viscosity`, `speedOfSound`, `area`
    - `reynolds`, `mach`
    - `baseDragCoefficient`, `dragCoefficient`, `dragForce`

- `drag.metrics`
  - includes:
    - `range`
    - `maxHeight`
    - `flightTime`
    - `finalSpeed`
    - `peak`

- `drag.aero`
  - includes:
    - `projectileMass`
    - `projectileShape`
    - `dragModel`
    - `ballisticCoefficient`
    - `airDensity`
    - `viscosity`
    - `area`
    - `launchReynolds`
    - `launchDragCoefficient`
    - `launchDragForce`
    - `impactReynolds`
    - `impactDragCoefficient`
    - `impactDragForce`

- `focusedBounds`
  - plot bounds computed around the current shot

- `stableBounds`
  - fixed historical/overall plot bounds
  - if `currentGun` matches a historical launcher key, the response uses that launcher's stable bounds

## Error Cases

### `401 Unauthorized`

Returned by `POST /api/simulate` when:
- no valid API key is present
- no valid browser session is present
- browser-session request is missing `X-CSRF-Token`
- forged cookie plus derived CSRF is attempted

Response body:

```json
{
  "error": "Unauthorized."
}
```

### `403 Forbidden`

Returned when:
- `Origin` is not allowed
- bootstrap answer is incorrect

Typical response body:

```json
{
  "error": "Origin not allowed."
}
```

### Validation / Request Errors

`400 Bad Request` is returned for invalid request content, including:
- invalid JSON body
- non-object JSON payload
- invalid `Content-Length`
- non-numeric numeric fields
- invalid or expired bootstrap challenge token

`413 Payload Too Large` is returned when the request body exceeds the configured maximum.

Validation errors are returned as JSON:

```json
{
  "error": "message"
}
```

## Scope

This is a lightweight internal/browser contract document, not a full OpenAPI specification.
