import React, { useState } from "react";

const SAMPLE_SCRIPT = `SCENE 12 - EXT. ABANDONED WAREHOUSE - DAY

JACK (30s, rugged) and SARAH (20s, determined) enter through a rusted door.

JACK
This place hasn't been touched in years.

SARAH
Perfect. The device will be hidden in the basement.

JACK pulls out a flashlight. WATER drips from the ceiling.

SARAH
(whispering)
Did you hear that?

A LOUD CRASH from upstairs. They freeze.

JACK
We need to move. Now.`;

export default function ScriptUpload({ apiUrl, onAnalyzed }) {
  const [scriptText, setScriptText] = useState(SAMPLE_SCRIPT);
  const [shootDate, setShootDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/api/upload-script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script_text: scriptText,
          shoot_start_date: shootDate || null,
        }),
      });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();
      onAnalyzed(data.reports);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-panel">
      <textarea
        value={scriptText}
        onChange={(e) => setScriptText(e.target.value)}
        spellCheck={false}
      />
      <div className="row">
        <input
          type="date"
          value={shootDate}
          onChange={(e) => setShootDate(e.target.value)}
        />
        <button className="primary" onClick={submit} disabled={loading}>
          {loading ? "Analyzing script…" : "Run production analysis"}
        </button>
        {error && <span style={{ color: "var(--risk-high)", fontSize: 13 }}>{error}</span>}
      </div>
    </div>
  );
}
