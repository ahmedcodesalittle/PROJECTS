import { useState, useRef, useEffect } from "react";

// Bin-style colour coding for each of the 12 classes. Mirrors the way real
// kerbside schemes colour-code streams, which makes the result scannable.
const CATEGORY_COLORS = {
  paper: "#3b82c4",
  cardboard: "#a16207",
  biological: "#4d7c0f",
  metal: "#64748b",
  plastic: "#0891b2",
  "green-glass": "#15803d",
  "brown-glass": "#78350f",
  "white-glass": "#94a3b8",
  clothes: "#9333ea",
  shoes: "#7c3aed",
  batteries: "#dc2626",
  trash: "#44403c",
};

const prettify = (s) =>
  s.replace("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [modelReady, setModelReady] = useState(null);
  const inputRef = useRef(null);

  // Check the backend on load so we can warn early if the model isn't there.
  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setModelReady(d.model_loaded))
      .catch(() => setModelReady(false));
  }, []);

  const chooseFile = (f) => {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    setPreview(URL.createObjectURL(f));
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    chooseFile(e.dataTransfer.files?.[0]);
  };

  const classify = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = new FormData();
      body.append("image", file);
      const res = await fetch("/api/predict", { method: "POST", body });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong.");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const topColor = result ? CATEGORY_COLORS[result.prediction] : "#137a6e";

  return (
    <div className="page">
      <header className="masthead">
        <div className="wordmark">
          <span className="mark" aria-hidden="true" />
          Sortwise
        </div>
        <p className="tagline">
          Point it at a piece of waste. It tells you which bin it belongs in.
        </p>
      </header>

      {modelReady === false && (
        <div className="banner">
          The model isn’t loaded yet. Train it on Kaggle, then drop
          <code> garbage_model.keras </code> and <code> class_names.json </code>
          into <code>backend/models/</code> and restart the server.
        </div>
      )}

      <main className="stage">
        {/* ---- Upload side ---- */}
        <section className="panel upload-panel">
          <div
            className={`dropzone ${dragging ? "is-dragging" : ""} ${
              preview ? "has-image" : ""
            }`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            role="button"
            tabIndex={0}
            onKeyDown={(e) =>
              (e.key === "Enter" || e.key === " ") && inputRef.current?.click()
            }
          >
            {preview ? (
              <img src={preview} alt="Selected item" className="preview" />
            ) : (
              <div className="dropzone-empty">
                <span className="plus">+</span>
                <p className="drop-title">Drop an image here</p>
                <p className="drop-sub">or click to browse · JPG, PNG, WEBP</p>
              </div>
            )}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => chooseFile(e.target.files?.[0])}
          />

          <div className="actions">
            <button
              className="btn primary"
              onClick={classify}
              disabled={!file || loading}
            >
              {loading ? "Reading the image…" : "Classify"}
            </button>
            {file && (
              <button className="btn ghost" onClick={reset} disabled={loading}>
                Clear
              </button>
            )}
          </div>

          {error && <p className="error">{error}</p>}
        </section>

        {/* ---- Result side ---- */}
        <section className="panel result-panel">
          {!result && !loading && (
            <div className="placeholder">
              <p>The sorting label appears here once you classify an item.</p>
            </div>
          )}

          {loading && (
            <div className="placeholder">
              <div className="spinner" />
              <p>Working it out…</p>
            </div>
          )}

          {result && (
            <article
              className="label-card"
              style={{ "--cat": topColor }}
            >
              <div className="label-stripe" />
              <div className="label-body">
                <span className="eyebrow">Detected material</span>
                <h2 className="verdict">{prettify(result.prediction)}</h2>

                <div className="confidence">
                  <div className="conf-track">
                    <div
                      className="conf-fill"
                      style={{ width: `${(result.confidence * 100).toFixed(0)}%` }}
                    />
                  </div>
                  <span className="conf-num">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <dl className="facts">
                  <div>
                    <dt>Goes in</dt>
                    <dd>{result.guidance?.bin || "—"}</dd>
                  </div>
                  <div>
                    <dt>Recyclable</dt>
                    <dd>
                      <span
                        className={`pill ${
                          result.guidance?.recyclable ? "yes" : "no"
                        }`}
                      >
                        {result.guidance?.recyclable ? "Yes" : "No"}
                      </span>
                    </dd>
                  </div>
                </dl>

                {result.guidance?.tip && (
                  <p className="tip">{result.guidance.tip}</p>
                )}

                <div className="runners">
                  <span className="runners-label">Other possibilities</span>
                  <ul>
                    {result.distribution.slice(1, 4).map((d) => (
                      <li key={d.label}>
                        <span
                          className="dot"
                          style={{ background: CATEGORY_COLORS[d.label] }}
                        />
                        {prettify(d.label)}
                        <span className="runner-conf">
                          {(d.confidence * 100).toFixed(1)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </article>
          )}
        </section>
      </main>

      <footer className="foot">
        Trained on the 12-class Garbage Classification dataset · MobileNetV2
        transfer learning · Flask + React
      </footer>
    </div>
  );
}
