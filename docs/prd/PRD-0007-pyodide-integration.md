# PRD: Pyodide Integration for FLAT Format Validator

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy v0.3.0
**Depends on:** PRD `flat-validator` (v0.2.0) — core `FlatValidator` Python module must exist
**Author:** Chregi
**Date:** 2026-03-12

---

## 1. Overview

### 1.1 Background

In v0.2.0, the GitHub Pages validator (`validator.html`) ships with a JavaScript reimplementation of the validation logic. This works, but creates a **maintenance split**: any bug fix or new validation rule added to the Python `FlatValidator` must be manually ported to JS. Over time, the two implementations will diverge.

[Pyodide](https://pyodide.org) is a WebAssembly port of CPython that runs in the browser. It allows the web validator to execute the **actual oehrpy Python code** — no JS reimplementation, no drift, guaranteed parity.

### 1.2 Goal

Replace the JavaScript validation engine in `validator.html` with a Pyodide runtime that loads `oehrpy` from PyPI and calls `FlatValidator` directly. The web UI stays identical; only the execution engine changes.

### 1.3 Why This Matters

- **Single source of truth**: The Python implementation is the reference. The web tool stops being a translation and becomes a thin UI wrapper.
- **Automatic updates**: When oehrpy releases v0.4.0 with new validation rules, the web tool picks them up on the next page load — no HTML changes needed.
- **Trust**: Clinical developers can verify that what the web tool says matches what the Python SDK will do in their production code.
- **Community demos**: Anyone can test their templates without installing Python — lowering the barrier to oehrpy adoption.

---

## 2. Goals and Non-Goals

### Goals

| Goal | Priority |
|------|----------|
| Run `oehrpy.validation.FlatValidator` directly in the browser | P0 |
| Load oehrpy from PyPI via Pyodide's `micropip` | P0 |
| Maintain identical web UI from v0.2.0 | P0 |
| Show meaningful progress during the ~5-10s cold load | P0 |
| Cache the Pyodide + oehrpy bundle across page reloads | P1 |
| Graceful fallback to JS engine if Pyodide fails to load | P1 |
| Allow pinning to a specific oehrpy version | P2 |
| Support offline use after first load (service worker cache) | P2 |

### Non-Goals

- Replacing the Python CLI — this is browser-only
- Running EHRBase REST API calls from the browser (network security model makes this impractical without a proxy)
- Supporting Python 2 or Pyodide versions older than 0.25

---

## 3. User Stories

### openEHR developer, no Python installed

> *"I'm on a Windows machine without Python. I want to paste my Web Template and FLAT composition and get the same validation the oehrpy SDK would give me — without setting anything up."*

### Team lead reviewing a PR

> *"I want to send my colleague a link to the validator with a pre-loaded example. They should get the exact same errors that our CI pipeline shows."*

### SDK contributor

> *"I added a new validation rule to FlatValidator in Python. I don't want to also update a JS file. The web tool should just work with my new rule."*

---

## 4. Functional Requirements

### 4.1 Pyodide Runtime Bootstrap

On page load, the tool must:

1. Load the Pyodide runtime from the official CDN (`cdn.jsdelivr.net/pyodide/`)
2. Use `micropip` to install `oehrpy` (latest stable, or a pinned version — see Section 4.5)
3. Import `oehrpy.validation` into the Python namespace
4. Signal readiness to the UI

The bootstrap sequence runs **once per session**. Subsequent validations re-use the live Python runtime without reloading.

### 4.2 Validation Bridge

Implement a thin JavaScript <-> Python bridge:

```javascript
// JS side — calls Python
async function runPythonValidation(wtJson, flatObj, platform) {
  const result = await pyodide.runPythonAsync(`
    import json
    from openehr_sdk.validation import FlatValidator

    wt = json.loads('''${JSON.stringify(wtJson)}''')
    flat = json.loads('''${JSON.stringify(flatObj)}''')

    validator = FlatValidator.from_web_template(wt, platform="${platform}")
    result = validator.validate(flat)

    json.dumps({
      "is_valid": result.is_valid,
      "errors": [
        {
          "path": e.path,
          "error_type": e.error_type,
          "message": e.message,
          "suggestion": e.suggestion,
          "valid_alternatives": e.valid_alternatives,
        }
        for e in result.errors
      ],
      "warnings": [
        {
          "path": w.path,
          "error_type": w.error_type,
          "message": w.message,
          "suggestion": w.suggestion,
        }
        for w in result.warnings
      ],
      "valid_path_count": result.valid_path_count,
      "checked_path_count": result.checked_path_count,
      "template_id": result.template_id,
    })
  `);
  return JSON.parse(result);
}
```

The bridge must handle Python exceptions gracefully and surface them as UI error messages (not browser console crashes).

### 4.3 Loading State UX

Cold start takes 5-15 seconds (Pyodide runtime ~8MB + oehrpy install). The UI must:

- Show a loading overlay with a progress indicator when the page first opens
- Display step-by-step progress: `Loading Python runtime... -> Installing oehrpy... -> Ready`
- Disable the Validate button until the runtime is ready
- Once ready, show an unobtrusive status indicator (e.g., a green dot labeled `Python 3.x . oehrpy vX.Y.Z`) in the footer
- Never block paste/editing of the JSON panels during loading

### 4.4 Fallback to JavaScript Engine

If Pyodide fails to initialize (network unavailable, browser incompatibility, timeout after 30s), the tool must:

- Automatically fall back to the built-in JavaScript validation engine
- Show a non-blocking toast: `"Python runtime unavailable — using built-in validator (may differ from SDK)"`
- Log the failure reason to the browser console
- Allow the user to manually retry loading Pyodide via a "Retry Python" button in the footer

The JS fallback ensures the tool is always usable, even on restricted networks.

### 4.5 Version Pinning

Add a `?version=0.2.0` URL query parameter that overrides the oehrpy version installed via `micropip`. This allows:

- Linking to the validator with a specific SDK version (useful for bug reports, regression testing)
- Comparing behavior between versions by opening two tabs

If no version is specified, install the latest stable release from PyPI.

The current version in use must be visible in the UI footer.

### 4.6 Valid Paths from Python

The path explorer panel (introduced in v0.2.0) must be populated from the Python-computed valid path set:

```python
# Python
paths = validator.enumerate_paths()
# Returns list of {"path": str, "rm_type": str, "name": str}
```

This ensures the explorer shows exactly what the Python engine considers valid — no discrepancy with the JS path list from v0.2.0.

---

## 5. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Cold start time (first load, uncached) | < 15s on a 10 Mbps connection |
| Warm start time (Pyodide cached, oehrpy cached) | < 2s |
| Validation execution time (post-load) | < 500ms for 50-field composition |
| Pyodide version | 0.26+ (Python 3.12) |
| Browser support | Chrome 90+, Firefox 88+, Safari 15+, Edge 90+ |
| Mobile support | Functional (not primary target) |
| Bundle size impact on cold load | Documented clearly in UI ("~10MB first load") |

---

## 6. Technical Design

### 6.1 Pyodide Loading Strategy

```
Page load
  |
  +- [Immediate] Render UI, enable JSON panels
  |
  +- [Background] loadPyodide()
       |
       +- Check IndexedDB cache for pyodide + oehrpy wheels
       |    +- Cache HIT -> load from cache (~1-2s)
       |    +- Cache MISS -> fetch from CDN (~8-12s)
       |
       +- micropip.install("oehrpy==<pinned_or_latest>")
       |
       +- Signal ready -> enable Validate button
```

Use `pyodide.loadPackage` for pure-Python packages and `micropip` for packages not in the Pyodide distribution. `oehrpy` has no compiled C extensions (pure Python + Pydantic), so `micropip` install will work.

### 6.2 Caching Strategy

Use the browser's Cache API (via a lightweight service worker) to cache:

- The Pyodide WebAssembly bundle
- The oehrpy wheel file from PyPI

Cache key includes the oehrpy version string. On version upgrade (new `?version=` param or new PyPI release detected), re-fetch only the oehrpy wheel (not the full Pyodide runtime).

### 6.3 Pydantic in Pyodide

Pydantic v2 uses a Rust extension (`pydantic-core`). As of Pyodide 0.26, `pydantic-core` is available as a pre-built wheel in the Pyodide distribution. Verify at implementation time that the installed Pyodide version includes it; if not, pin Pyodide to a version that does, or investigate pure-Python fallback (`pydantic` v1 compat mode).

This is the **primary technical risk** of this feature — see Section 8.

### 6.4 Data Serialization Boundary

Python objects cannot be passed directly to JavaScript. All data crossing the Python <-> JS boundary must be serialized to JSON strings. The bridge (Section 4.2) handles this via `json.dumps` on the Python side and `JSON.parse` on the JS side.

Large Web Templates (some openEHR templates have 200+ nodes) may produce large JSON blobs. Keep an eye on serialization overhead; if it becomes a bottleneck, consider streaming results incrementally.

### 6.5 HTML File Structure

The `validator.html` file will grow significantly. Organize it as:

```
validator.html
  +-- <head> — styles (unchanged from v0.2.0)
  +-- <body> — UI markup (unchanged from v0.2.0)
  +-- <script>
       +-- // === UI LAYER (unchanged) ===
       +-- // === PYTHON BRIDGE ===
       +-- // === PYODIDE BOOTSTRAP ===
       +-- // === JS FALLBACK ENGINE (kept from v0.2.0) ===
```

Keep the JS fallback engine intact — it doubles as the offline/error fallback and as a reference for testing parity between implementations.

---

## 7. Implementation Plan

### Phase 3A — Pyodide Proof of Concept

| Task | Effort | Notes |
|------|--------|-------|
| Verify Pydantic v2 works in Pyodide 0.26 | 0.5 day | Blocking — must resolve before proceeding |
| Basic Pyodide bootstrap in validator.html | 0.5 day | |
| micropip install oehrpy, smoke test | 0.5 day | |
| Basic bridge: call FlatValidator from JS | 1 day | |
| **Subtotal** | **2.5 days** | |

### Phase 3B — Full Integration

| Task | Effort |
|------|--------|
| Loading state UX (progress steps, disable/enable) | 1 day |
| JS fallback with toast notification | 0.5 day |
| Cache API service worker for Pyodide + oehrpy | 1 day |
| Version pinning via URL param | 0.5 day |
| Path explorer fed from Python enumerate_paths() | 0.5 day |
| Cross-browser testing | 1 day |
| **Subtotal** | **4.5 days** |

**Total: ~7 days**

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pydantic v2 (Rust extension) not available in Pyodide | Medium | High | Pin to Pyodide version with pydantic-core; or add `pydantic` v1 compat as fallback in oehrpy |
| Pyodide load time too slow for real-world use | Low | Medium | Aggressive caching; show clear progress; keep JS fallback |
| micropip install fails on restricted networks (CDN blocked) | Medium | Medium | JS fallback handles this transparently |
| oehrpy API changes break the bridge | Low | Low | Bridge is thin (one function call); update when oehrpy API changes |
| Pyodide security model blocks certain Python stdlib operations | Low | Low | FlatValidator only uses stdlib `json` and `difflib` — no file I/O or network |

---

## 9. Success Metrics

- Web tool returns identical results to `oehrpy validate-flat` CLI for the same inputs
- Cold load completes in < 12s on a standard connection (verified on Chrome, Firefox, Safari)
- Zero divergences reported between web tool and Python CLI over 3 months post-launch
- Pyodide runtime version and oehrpy version visible in tool footer

---

## 10. Open Questions

| Question | Owner | Decision needed by |
|----------|-------|--------------------|
| Is pydantic-core available in Pyodide 0.26? | Chregi | Phase 3A start |
| Should we maintain the JS fallback engine long-term, or deprecate it once Pyodide is stable? | Chregi | Phase 3B end |
| Should the service worker cache be opt-in (privacy-conscious users may prefer no caching)? | Chregi | Phase 3B start |
| Should we host our own Pyodide CDN mirror for reliability? | Chregi | Phase 3B start |

---

## Appendix: Pyodide Compatibility Reference

As of Pyodide 0.26 (Python 3.12):

| Package | Available | Notes |
|---------|-----------|-------|
| `pydantic` v2 | Yes (check) | Requires `pydantic-core` Rust extension |
| `pydantic-core` | Check 0.26 release notes | Key blocker |
| `httpx` | Yes via micropip | Not needed for validator |
| `difflib` | Yes stdlib | Used for fuzzy suggestions |
| `json` | Yes stdlib | Used for bridge serialization |
| `dataclasses` | Yes stdlib | Used by ValidationResult |

Always verify against the [Pyodide packages list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) at implementation time.
