import { useEffect, useState } from "react";
import { fetchHistory, fetchHistoryRecord, submitPrediction, SUPPORTED_CROPS } from "./api.js";
import { calculateHistoryAnalytics, displayClass, errorMessage, formatDate, MAX_UPLOAD_BYTES, safeExternalUrl, safeImageDataUrl, validateImageFile, validateLesionMask } from "./workflow.js";

function StatusPill({ children, tone = "neutral" }) {
  return <span className={`status-pill status-${tone}`}><span aria-hidden="true" />{children}</span>;
}
function Confidence({ value }) { return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—"; }
function Metric({ label, value }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
function SourceLinks({ sources = [] }) {
  if (!Array.isArray(sources)) return null;
  const links = sources.map((source, index) => ({ source, url: safeExternalUrl(source?.url), index })).filter((item) => item.url);
  if (!links.length) return null;
  return <div className="source-links">{links.map(({ source, url, index }) => <a key={url + "-" + index} href={url} target="_blank" rel="noreferrer">{source.title || source.organization || "Source"}<span aria-hidden="true"> ↗</span></a>)}</div>;
}

function CropSelector({ value, onChange }) {
  return (
    <div className="crop-selector" role="group" aria-labelledby="crop-selector-label">
      <span className="field-label" id="crop-selector-label">CROP <span className="required-label">REQUIRED</span></span>
      <div className="crop-options">
        {SUPPORTED_CROPS.map((crop) => (
          <label key={crop} className={`crop-option${value === crop ? " crop-option-selected" : ""}`}>
            <input
              type="radio"
              name="crop"
              value={crop}
              checked={value === crop}
              onChange={() => onChange(crop)}
            />
            {crop.charAt(0).toUpperCase() + crop.slice(1)}
          </label>
        ))}
      </div>
    </div>
  );
}

export function PredictionResult({ result }) {
  if (!result) return null;
  const prediction = result.prediction || {};
  const disease = result.disease_information;
  const probabilities = Object.entries(prediction.probabilities || {}).sort((a, b) => b[1] - a[1]);
  const heatmap = safeImageDataUrl(result.explainability?.heatmap_data_url);
  const overlay = safeImageDataUrl(result.explainability?.overlay_data_url);
  const severity = result.severity || {};
  const weather = result.weather_context || {};
  const measures = weather.weather;
  const cropLabel = result.crop ? result.crop.charAt(0).toUpperCase() + result.crop.slice(1) : null;
  return <section className="result-stack" aria-labelledby="result-heading" data-testid="prediction-result">
    <div className="result-heading-row"><div><p className="eyebrow">ANALYSIS RESULT</p><h2 id="result-heading">Your crop health summary</h2></div><StatusPill tone={result.recommendation_status === "available" ? "good" : "warning"}>{result.prediction_status === "low_confidence" ? "Low confidence" : result.recommendation_status === "safe_fallback" ? "Limited result" : "Analysis saved"}</StatusPill></div>
    <article className="result-card prediction-card">
      <div className="prediction-main"><div className="leaf-icon" aria-hidden="true">✳</div><div><span className="field-label">PREDICTED CLASS</span><h3>{displayClass(prediction.class_id) || "Class unavailable"}</h3><p>{disease?.crop && disease?.name ? `${disease.crop} · ${disease.name}` : "No supported disease details were provided for this class."}</p></div></div>
      <div className="prediction-stats"><div><span className="field-label">CONFIDENCE</span><strong>{Confidence({ value: prediction.confidence })}</strong></div><div><span className="field-label">MODEL VERSION</span><strong>{result.model?.version || "Not reported"}</strong></div>{cropLabel && <div><span className="field-label">CROP</span><strong>{cropLabel}</strong></div>}<div><span className="field-label">HISTORY ID</span><strong className="record-id">{result.history?.record_id || "Not saved"}</strong></div></div>
      {result.prediction_status === "low_confidence" && <p className="inline-note">Confidence is below the configured recommendation threshold. Disease-specific guidance is withheld.</p>}
      {result.prediction_status === "unsupported_disease" && <p className="inline-note">This class is not covered by the supported disease information.</p>}
    </article>
    <div className="results-grid">
      <article className="result-card"><SectionTitle number="01" label="DISEASE INFORMATION" title={disease?.name || "No disease details"} /><p className="body-copy">{disease?.description || "The prediction did not map to a supported knowledge-base entry."}</p>{disease?.symptoms?.length > 0 && <ul className="compact-list">{disease.symptoms.map((item) => <li key={item}>{item}</li>)}</ul>}<SourceLinks sources={disease?.trace?.sources} /></article>
      <article className="result-card"><SectionTitle number="02" label="SEVERITY" title={severity.status === "estimated" ? severity.estimate?.category || "Estimated" : severity.status === "unavailable" ? "Unavailable" : "Not estimated"} />{severity.status === "estimated" ? <p className="body-copy">Affected area estimate: {Number(severity.estimate?.severity_percentage).toFixed(1)}%. This image-processing estimate is provisional.</p> : <p className="body-copy">{severity.status === "not_requested" ? "Severity needs an aligned lesion mask. Upload an optional PNG mask with the leaf image to request an estimate." : "Severity could not be estimated from this input."}</p>}</article>
    </div>
    {probabilities.length > 0 && <article className="result-card probability-card"><SectionTitle number="03" label="MODEL SCORES" title="Class probabilities" /><div className="probability-list">{probabilities.map(([classId, value]) => <div className="probability-row" key={classId}><span>{displayClass(classId)}</span><div className="probability-track"><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} /></div><strong>{Confidence({ value })}</strong></div>)}</div></article>}
    <article className="result-card guidance-card"><SectionTitle number="04" label="GENERAL GUIDANCE" title="Prevention and management" />{result.general_guidance?.length ? <ul className="guidance-list">{result.general_guidance.map((item) => <li key={item.id || item.text}><span>{item.category?.replaceAll("_", " ") || "Guidance"}</span><p>{item.text}</p><SourceLinks sources={item.trace?.sources} /></li>)}</ul> : <p className="body-copy">No disease-specific guidance is available for this result. Consult a local agricultural extension professional if you are concerned.</p>}</article>
    <div className="results-grid">
      <article className="result-card weather-card"><SectionTitle number="05" label="WEATHER CONTEXT" title={weather.status === "available" ? weather.location?.name || "Current conditions" : weather.status === "not_requested" ? "Not requested" : "Unavailable"} />{measures ? <><div className="weather-metrics"><Metric label="Temperature" value={`${measures.temperature_c}°C`} /><Metric label="Humidity" value={`${measures.relative_humidity_percent}%`} /><Metric label="Precipitation" value={`${measures.precipitation_mm} mm`} /><Metric label="Wind" value={`${measures.wind_speed_kmh} km/h`} /></div><p className="muted-small">Observed {formatDate(weather.observed_at)} · context only, not evidence of cause.</p></> : <p className="body-copy">{result.recommendation_message || "No current weather values are available."}</p>}{result.weather_guidance?.length > 0 && <div className="weather-guidance">{result.weather_guidance.map((item) => <p key={item.id}>{item.text}<SourceLinks sources={item.trace?.sources} /></p>)}</div>}{measures && result.weather_guidance?.length === 0 && <p className="muted-small">No configured weather context matched these observations. Weather does not establish disease causation.</p>}</article>
      <article className="result-card explain-card"><SectionTitle number="06" label="EXPLAINABILITY" title="Grad-CAM view" />{heatmap || overlay ? <div className="cam-grid">{heatmap && <figure><img src={heatmap} alt="Grad-CAM heatmap highlighting model activation areas" /><figcaption>Activation heatmap</figcaption></figure>}{overlay && <figure><img src={overlay} alt="Grad-CAM heatmap overlaid on the uploaded leaf image" /><figcaption>Overlay preview</figcaption></figure>}</div> : <p className="body-copy">Explainability image is unavailable for this result.</p>}<p className="muted-small">Grad-CAM visualizes model activation; it does not prove biological cause.</p></article>
    </div>
    {result.recommendation_message && <p className="recommendation-note" role="status">{result.recommendation_message}</p>}
  </section>;
}

function SectionTitle({ number, label, title }) { return <div className="section-title"><span className="section-icon">{number}</span><div><span className="field-label">{label}</span><h3>{title}</h3></div></div>; }

export function AnalyticsPanel({ rows }) {
  const analytics = calculateHistoryAnalytics(rows);
  if (!analytics.total) return <section className="analytics-card" aria-label="History analytics"><h3>History analytics</h3><p className="analytics-empty">Analytics will appear when prediction history contains records.</p></section>;
  const maxClass = Math.max(1, ...Object.values(analytics.classDistribution));
  const maxSeverity = Math.max(1, ...Object.values(analytics.severityDistribution));
  return <section className="analytics-card" aria-label="History analytics"><div className="analytics-heading"><div><p className="eyebrow">RECORDED DATA</p><h3>History analytics</h3></div><span>Current page · {analytics.total} records</span></div>
    <div className="analytics-metrics"><Metric label="Predictions on page" value={analytics.total} /><Metric label="Unique classes" value={analytics.uniqueClasses} /><Metric label="Average confidence" value={analytics.averageConfidence === null ? "—" : Confidence({ value: analytics.averageConfidence })} /></div>
    <div className="analytics-charts"><Distribution title="Class distribution" values={analytics.classDistribution} max={maxClass} /><Distribution title="Severity distribution" values={analytics.severityDistribution} max={maxSeverity} empty="No severity estimates on this page." /></div>
  </section>;
}

function Distribution({ title, values, max, empty = "No recorded values." }) {
  const entries = Object.entries(values).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  return <div className="distribution"><h4>{title}</h4>{entries.length ? <div role="img" aria-label={title + " based on current page records"} className="distribution-list">{entries.map(([key, count]) => <div className="distribution-row" key={key}><span>{displayClass(key)}</span><span className="distribution-track"><i style={{ width: ((count / max) * 100) + "%" }} /></span><strong>{count}</strong></div>)}</div> : <p className="analytics-empty">{empty}</p>}</div>;
}

export function HistoryPanel({ rows, loading, error, selected, selectedLoading, selectedError, onOpen, onRefresh, page, hasMore, onPageChange, classFilter, onClassFilterChange, onFilterSubmit }) {
  return <>
    <div className="history-heading"><div><p className="eyebrow">SAVED ANALYSES</p><h2 id="history-heading">Prediction history</h2><p>Recorded predictions from the backend, newest first.</p></div><button className="button button-light" onClick={onRefresh} disabled={loading}>Refresh</button></div>
    <AnalyticsPanel rows={rows} />
    <section aria-label="History records" className="history-records">
      <form className="history-filters" onSubmit={(event) => { event.preventDefault(); onFilterSubmit(); }}><label htmlFor="class-filter">Filter by class ID</label><input id="class-filter" list="history-class-options" value={classFilter} onChange={(event) => onClassFilterChange(event.target.value)} placeholder="All classes" /><datalist id="history-class-options">{[...new Set(rows.map((row) => row.predicted_class_id))].map((classId) => <option value={classId} key={classId} />)}</datalist><button className="button button-light" type="submit" disabled={loading}>Apply</button>{classFilter && <button className="text-button" type="button" onClick={() => { onClassFilterChange(""); onFilterSubmit(""); }}>Clear filter</button>}</form>
      {loading && <div className="state-panel" role="status"><span className="spinner" />Loading prediction history…</div>}
      {!loading && error && <div className="state-panel state-error" role="alert"><strong>History could not be loaded</strong><p>{error}</p><button className="button button-light" onClick={onRefresh}>Try again</button></div>}
      {!loading && !error && rows.length === 0 && <div className="state-panel empty-state"><div aria-hidden="true">◷</div><strong>{classFilter ? "No matching predictions" : "No predictions yet"}</strong><p>{classFilter ? "Try a different class ID or clear the filter." : "Completed analyses will appear here after the API saves them."}</p></div>}
      {!loading && !error && rows.length > 0 && <div className="history-table-wrap"><table><thead><tr><th>Date</th><th>Predicted class</th><th>Confidence</th><th>Severity</th><th>Weather</th><th>Model</th><th /></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{formatDate(row.created_at)}</td><td><strong>{displayClass(row.predicted_class_id)}</strong></td><td>{Confidence({ value: row.confidence })}</td><td>{row.severity?.category || row.severity?.status || "—"}</td><td>{row.weather_context?.status || "Not available"}</td><td>{row.model_version || "—"}</td><td><button className="text-button" onClick={() => onOpen(row.id)}>Open result <span aria-hidden="true">→</span></button></td></tr>)}</tbody></table></div>}
      {!loading && !error && <nav className="history-pagination" aria-label="History pages"><button className="button button-light" disabled={loading || page === 0} onClick={() => onPageChange(page - 1)}>Previous</button><span>Page {page + 1}</span><button className="button button-light" disabled={loading || !hasMore} onClick={() => onPageChange(page + 1)}>Next</button></nav>}
    </section>
    <aside className="history-detail" aria-live="polite" aria-label="Prediction detail">
      {!selected && !selectedLoading && !selectedError && <div className="detail-placeholder"><span>↗</span><p>Select a history item to view its saved result details.</p></div>}
      {selectedLoading && <div className="state-panel" role="status"><span className="spinner" />Loading saved result…</div>}
      {selectedError && <div className="state-panel state-error" role="alert">{selectedError}</div>}
      {selected && !selectedLoading && <HistoryDetail selected={selected} />}
    </aside>
  </>;
}

function HistoryDetail({ selected }) {
  const rec = selected.recommendation_result || {};
  const disease = rec.disease_information;
  const weather = selected.weather_context || rec.weather_context || {};
  const severity = selected.severity || {};
  return <><p className="eyebrow">SAVED RESULT</p><h3>{displayClass(selected.predicted_class_id)}</h3><p className="detail-date">{formatDate(selected.created_at)}</p><div className="detail-metrics"><Metric label="Confidence" value={Confidence({ value: selected.confidence })} /><Metric label="Model version" value={selected.model_version || "Not reported"} /><Metric label="Severity status" value={severity.status || (severity.category ? "estimated" : "not recorded")} /><Metric label="Severity category" value={severity.category || "Not estimated"} />{typeof severity.severity_percentage === "number" && <Metric label="Affected area" value={severity.severity_percentage.toFixed(1) + "%"} />}</div>
    <DetailSection title="Disease information">{disease ? <><strong>{disease.crop ? disease.crop + " · " : ""}{disease.name || displayClass(disease.id || "")}</strong>{disease.description && <p>{disease.description}</p>}{Array.isArray(disease.symptoms) && disease.symptoms.length > 0 && <><span className="detail-label">Symptoms</span><ul>{disease.symptoms.map((item) => <li key={item}>{item}</li>)}</ul></>}{<Trace trace={disease.trace} />}</> : <p>Disease information was not stored for this record.</p>}</DetailSection>
    <DetailSection title="General guidance">{Array.isArray(rec.general_guidance) && rec.general_guidance.length ? <ul className="detail-guidance">{rec.general_guidance.map((item, index) => <li key={item.id || index}><span className="detail-label">{item.category || "Guidance"}</span><p>{item.text}</p><Trace trace={item.trace} /></li>)}</ul> : <p>No stored general guidance.</p>}</DetailSection>
    <DetailSection title="Weather context">{weather.status === "available" ? <><p>Available{weather.location?.name ? " · " + weather.location.name : ""}{weather.observed_at ? " · " + formatDate(weather.observed_at) : ""}</p>{weather.weather && <p>{[weather.weather.temperature_c != null && weather.weather.temperature_c + "°C", weather.weather.relative_humidity_percent != null && weather.weather.relative_humidity_percent + "% humidity", weather.weather.precipitation_mm != null && weather.weather.precipitation_mm + " mm precipitation"].filter(Boolean).join(" · ")}</p>}</> : <p>{weather.status === "unavailable" ? "Weather data was unavailable for this prediction." : weather.status === "not_requested" ? "Weather was not requested." : "No weather data was stored."}</p>}</DetailSection>
    <DetailSection title="Recommendation">{rec.message && <p>{rec.message}</p>}{Array.isArray(rec.weather_guidance) && rec.weather_guidance.length ? <ul className="detail-guidance">{rec.weather_guidance.map((item, index) => <li key={item.id || index}><p>{item.text}</p><Trace trace={item.trace} /></li>)}</ul> : <p>No weather-specific guidance was stored.</p>}</DetailSection>
    <span className="detail-id">Record · {selected.id}</span>
  </>;
}

function DetailSection({ title, children }) { return <section className="detail-section"><h4>{title}</h4>{children}</section>; }
function Trace({ trace }) {
  if (!trace || typeof trace !== "object") return null;
  const sources = Array.isArray(trace.sources) ? trace.sources : [];
  const labels = [trace.rule_id && "Rule: " + trace.rule_id, trace.knowledge_base_entry_id && "Knowledge record: " + trace.knowledge_base_entry_id].filter(Boolean);
  if (!labels.length && !sources.length) return null;
  const links = sources.map((source, index) => ({ source, url: safeExternalUrl(source?.url), index })).filter((item) => item.url);
  if (!labels.length && !links.length) return null;
  return <div className="detail-trace">{labels.length > 0 && <p>{labels.join(" · ")}</p>}{links.map(({ source, url, index }) => <a key={url + "-" + index} href={url} target="_blank" rel="noreferrer">{source.title || source.organization || "Source"}</a>)}</div>;
}

export default function App() {
  const [activeView, setActiveView] = useState("analyze");
  const [crop, setCrop] = useState("tomato");
  const [image, setImage] = useState(null); const [lesionMask, setLesionMask] = useState(null);
  const [location, setLocation] = useState(""); const [formError, setFormError] = useState(""); const [maskError, setMaskError] = useState("");
  const [result, setResult] = useState(null); const [submitting, setSubmitting] = useState(false); const [previewUrl, setPreviewUrl] = useState("");
  const [historyRows, setHistoryRows] = useState([]); const [historyLoading, setHistoryLoading] = useState(false); const [historyError, setHistoryError] = useState("");
  const [selected, setSelected] = useState(null); const [selectedLoading, setSelectedLoading] = useState(false); const [selectedError, setSelectedError] = useState(""); const [refreshToken, setRefreshToken] = useState(0);
  const [historyPage, setHistoryPage] = useState(0); const [historyHasMore, setHistoryHasMore] = useState(false);
  const [classFilter, setClassFilter] = useState(""); const [appliedClassFilter, setAppliedClassFilter] = useState("");

  useEffect(() => {
    if (!image) { setPreviewUrl(""); return undefined; }
    const url = URL.createObjectURL(image); setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  useEffect(() => {
    if (activeView !== "history") return undefined;
    const controller = new AbortController(); setHistoryLoading(true); setHistoryError(""); setHistoryRows([]); setHistoryHasMore(false);
    fetchHistory({ limit: 21, offset: historyPage * 20, classId: appliedClassFilter, signal: controller.signal }).then((data) => { setHistoryRows(data.items.slice(0, 20)); setHistoryHasMore(data.hasMore); }).catch((error) => { if (error.name !== "AbortError") { setHistoryRows([]); setHistoryHasMore(false); setHistoryError(errorMessage(error)); } }).finally(() => { if (!controller.signal.aborted) setHistoryLoading(false); });
    return () => controller.abort();
  }, [activeView, refreshToken, historyPage, appliedClassFilter]);

  function chooseImage(file) { const issue = validateImageFile(file); setImage(issue ? null : file); setResult(null); setFormError(issue || ""); }
  function chooseMask(file) { const issue = validateLesionMask(file); setLesionMask(issue ? null : file); setMaskError(issue || ""); }
  async function handleSubmit(event) {
    event.preventDefault(); const issue = validateImageFile(image); if (issue) { setFormError(issue); return; }
    setSubmitting(true); setFormError(""); setResult(null);
    try { setResult(await submitPrediction({ image, crop, lesionMask, location })); }
    catch (error) { setFormError(errorMessage(error)); }
    finally { setSubmitting(false); }
  }
  async function openRecord(recordId) {
    setSelected(null); setSelectedError(""); setSelectedLoading(true);
    try { setSelected(await fetchHistoryRecord(recordId)); }
    catch (error) { setSelectedError(errorMessage(error)); }
    finally { setSelectedLoading(false); }
  }
  function applyClassFilter(value = classFilter) { setClassFilter(value); setAppliedClassFilter(value.trim()); setHistoryPage(0); setSelected(null); setSelectedError(""); }
  function changeHistoryPage(nextPage) { setHistoryPage(Math.max(0, nextPage)); setSelected(null); setSelectedError(""); }
  const modelUnavailable = formError.toLowerCase().includes("production classifier is unavailable");

  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="#main" onClick={() => setActiveView("analyze")}><span className="brand-mark">✳</span><span>FIELDNOTES<small>CROP HEALTH</small></span></a><div className="sidebar-label">WORKSPACE</div><nav className="side-nav" aria-label="Main navigation"><button className={activeView === "analyze" ? "nav-item active" : "nav-item"} onClick={() => setActiveView("analyze")}><span>⌁</span>Leaf analysis</button><button className={activeView === "history" ? "nav-item active" : "nav-item"} onClick={() => setActiveView("history")}><span>◷</span>Prediction history</button></nav><div className="sidebar-foot"><span className="status-dot" /> RESEARCH PROTOTYPE<p>Model results are decision support and require field confirmation.</p></div></aside>
    <main id="main" className="main-content"><header className="topbar"><span className="breadcrumb">CROP HEALTH INTELLIGENCE <span>/</span> {activeView === "analyze" ? "ANALYZE" : "HISTORY"}</span><span className="topbar-tag">STAGES 0—14</span></header>
      {activeView === "analyze" ? <>
        <section className="page-intro"><div><p className="eyebrow">PLANT HEALTH INTELLIGENCE</p><h1>Understand what<br />your leaves are telling you.</h1><p>Upload a crop-leaf image for a model assessment, visual explanation, and source-linked guidance.</p></div><div className="api-state"><span className="api-state-icon">✳</span><div><strong>Inference API</strong><small>Model availability is verified at analysis time</small></div></div></section>
        <div className="prototype-notice"><span aria-hidden="true">ⓘ</span><p><strong>Research prototype.</strong> Production model availability is checked by the API. If no trained classifier is configured, the API reports it clearly; smoke-test weights are never used to produce predictions.</p></div>
        <section className="analysis-layout"><form className="upload-card" onSubmit={handleSubmit}>
          <div className="card-heading"><div><span className="step-index">01</span><h2>Leaf image</h2></div><span className="required-label">REQUIRED</span></div>
          <CropSelector value={crop} onChange={setCrop} />
          <label className={`dropzone ${previewUrl ? "has-preview" : ""}`} htmlFor="leaf-image" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseImage(event.dataTransfer.files?.[0] || null); }}><input id="leaf-image" aria-label="Leaf image" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={(event) => chooseImage(event.target.files?.[0] || null)} />{previewUrl ? <><img className="image-preview" src={previewUrl} alt="Selected leaf preview" /><span className="change-file">Choose a different image</span></> : <><span className="upload-icon" aria-hidden="true">↑</span><strong>Choose a leaf image</strong><span>or drag it here</span><small>JPEG, PNG or WEBP · Up to {Math.round(MAX_UPLOAD_BYTES / 1024 / 1024)} MB</small></>}</label>
          {image && <div className="file-summary"><span className="file-check">✓</span><span>{image.name}<small>{(image.size / 1024 / 1024).toFixed(2)} MB</small></span><button type="button" className="remove-file" aria-label="Remove leaf image" onClick={() => { setImage(null); setResult(null); setFormError(""); }}>×</button></div>}
          {formError && <div className={`form-error ${modelUnavailable ? "model-error" : ""}`} role="alert"><strong>{modelUnavailable ? "Production model unavailable" : "Unable to analyze image"}</strong><p>{formError}</p></div>}
          <div className="form-divider" /><label className="field-label" htmlFor="location">LOCATION <span className="optional-label">OPTIONAL</span></label><input id="location" className="text-input" type="text" maxLength={120} value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Town, region or nearest city" /><p className="input-hint">Used only to retrieve current weather context.</p>
          <div className="mask-upload-row"><div><label className="field-label" htmlFor="lesion-mask">LESION MASK <span className="optional-label">OPTIONAL</span></label><p className="input-hint">PNG mask aligned to the leaf image enables the current severity estimate.</p></div><label className="mask-button" htmlFor="lesion-mask">{lesionMask ? "Change mask" : "Add PNG mask"}<input id="lesion-mask" aria-label="Lesion mask PNG" type="file" accept=".png,image/png" onChange={(event) => chooseMask(event.target.files?.[0] || null)} /></label></div>
          {lesionMask && <div className="mask-selected">✓ {lesionMask.name}<button type="button" onClick={() => setLesionMask(null)}>Remove</button></div>}{maskError && <p className="field-error" role="alert">{maskError}</p>}
          <button className="button button-primary submit-button" type="submit" disabled={!image || submitting}>{submitting ? <><span className="spinner" /> Analyzing image…</> : <>Analyze leaf <span aria-hidden="true">→</span></>}</button><p className="privacy-note">Your uploaded file is processed temporarily and is not stored as an image.</p>
        </form><aside className="workflow-aside"><div className="aside-card"><p className="eyebrow">WHAT YOU’LL RECEIVE</p>{[["01", "Model assessment", "Predicted class, confidence and class scores."], ["02", "Visual explanation", "Grad-CAM highlights model activation areas."], ["03", "Evidence-linked context", "Knowledge-base guidance and optional weather context."], ["04", "Saved history", "Completed results can be reopened from history."]].map(([n, title, copy]) => <div className="workflow-step" key={n}><span>{n}</span><div><strong>{title}</strong><p>{copy}</p></div></div>)}</div><div className="aside-caution"><span>!</span><p>Image predictions are not a confirmed diagnosis. Weather context is not proof of disease cause. Consult local agricultural extension for decisions.</p></div></aside></section>
        {result && <PredictionResult result={result} />}
      </> : <HistoryPage rows={historyRows} loading={historyLoading} error={historyError} selected={selected} selectedLoading={selectedLoading} selectedError={selectedError} onOpen={openRecord} onRefresh={() => setRefreshToken((token) => token + 1)} page={historyPage} hasMore={historyHasMore} onPageChange={changeHistoryPage} classFilter={classFilter} onClassFilterChange={setClassFilter} onFilterSubmit={applyClassFilter} />}
      <footer className="app-footer"><span>DECISION SUPPORT RESEARCH</span><span>MODEL OUTPUTS REQUIRE FIELD CONFIRMATION</span></footer>
    </main>
  </div>;
}

function HistoryPage(props) { return <div className="history-page"><HistoryPanel {...props} /></div>; }
