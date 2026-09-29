"use client";

import { useState } from "react";

export default function Home() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [response, setResponse] = useState("");
  const [memories, setMemories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const [analystActions, setAnalystActions] = useState("");
  const [outcome, setOutcome] = useState("Resolved");
  const [feedback, setFeedback] = useState("");

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Fixed ID so server and browser render the same value
  const incidentId = "INC-001";

  const analyzeIncident = async () => {
    if (!title || !description) {
      alert("Please enter the incident title and description.");
      return;
    }

    setLoading(true);
    setSaved(false);

    try {
      const res = await fetch(
        "http://127.0.0.1:8000/incidents/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title,
            description,
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data.detail || "Something went wrong"
        );
      }

      setResponse(data.response);
      setMemories(data.memories_used || []);
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Unable to connect to backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const saveExperience = async () => {
    if (!analystActions || !feedback) {
      alert(
        "Please enter analyst actions and feedback."
      );
      return;
    }

    setSaving(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/incidents/${incidentId}/resolve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title,
            incident_description: description,
            ai_response: response,
            analyst_actions: analystActions,
            outcome,
            analyst_feedback: feedback,
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data.detail || "Unable to save experience"
        );
      }

      setSaved(true);
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Unable to save experience."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-6xl px-6 py-10">

        {/* HEADER */}
        <header className="mb-10">
          <div className="flex items-center gap-3">
            <span className="text-4xl">
              🛡️
            </span>

            <div>
              <h1 className="text-4xl font-bold">
                SecOps Memory
              </h1>

              <p className="mt-1 text-slate-400">
                AI-powered cybersecurity incident
                response with organizational memory
              </p>
            </div>
          </div>
        </header>

        {/* NEW INCIDENT */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

          <div className="flex items-center justify-between">

            <div>
              <h2 className="text-2xl font-semibold">
                New Security Incident
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Describe the incident and let the AI
                analyze it using previous organizational
                experience.
              </p>
            </div>

            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
              {incidentId}
            </span>

          </div>

          {/* TITLE */}
          <div className="mt-6">

            <label className="mb-2 block text-sm font-medium">
              Incident Title
            </label>

            <input
              value={title}
              onChange={(e) =>
                setTitle(e.target.value)
              }
              placeholder="Example: Credential Stuffing Attack"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
            />

          </div>

          {/* DESCRIPTION */}
          <div className="mt-5">

            <label className="mb-2 block text-sm font-medium">
              Incident Description
            </label>

            <textarea
              value={description}
              onChange={(e) =>
                setDescription(e.target.value)
              }
              placeholder="Describe what happened..."
              rows={6}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
            />

          </div>

          {/* ANALYZE BUTTON */}
          <button
            onClick={analyzeIncident}
            disabled={loading}
            className="mt-5 rounded-lg bg-blue-600 px-6 py-3 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Analyzing..."
              : "Analyze Incident"}
          </button>

        </section>

        {/* AI RESPONSE + MEMORY */}
        {response && (
          <>
            <div className="mt-8 grid gap-6 lg:grid-cols-2">

              {/* AI RESPONSE */}
              <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="text-2xl font-semibold">
                  🤖 AI Incident Response
                </h2>

                <pre className="mt-5 whitespace-pre-wrap font-sans text-sm leading-7 text-slate-300">
                  {response}
                </pre>

              </section>

              {/* HINDSIGHT MEMORY */}
              <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

                <h2 className="text-2xl font-semibold">
                  🧠 Historical Memory
                </h2>

                <p className="mt-2 text-sm text-slate-400">
                  Experiences recalled from Hindsight
                  for this incident.
                </p>

                {memories.length === 0 ? (

                  <p className="mt-5 text-slate-500">
                    No historical memories were found.
                  </p>

                ) : (

                  <div className="mt-5 max-h-[500px] space-y-4 overflow-y-auto">

                    {memories.map(
                      (memory, index) => (

                        <div
                          key={index}
                          className="rounded-lg border border-slate-700 bg-slate-950 p-4"
                        >

                          <p className="mb-2 text-xs font-semibold text-blue-400">
                            MEMORY {index + 1}
                          </p>

                          <p className="text-sm leading-6 text-slate-300">
                            {memory}
                          </p>

                        </div>

                      )
                    )}

                  </div>

                )}

              </section>

            </div>

            {/* RESOLVE INCIDENT */}
            <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">

              <h2 className="text-2xl font-semibold">
                ✅ Resolve Incident
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Tell the system what actually happened.
                This experience will be stored in
                Hindsight for future incidents.
              </p>

              {/* ANALYST ACTIONS */}
              <div className="mt-6">

                <label className="mb-2 block text-sm font-medium">
                  Actual Analyst Actions
                </label>

                <textarea
                  value={analystActions}
                  onChange={(e) =>
                    setAnalystActions(
                      e.target.value
                    )
                  }
                  placeholder="Example: Disabled the account, revoked active sessions, reset the password and enabled MFA."
                  rows={4}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-green-500"
                />

              </div>

              {/* OUTCOME */}
              <div className="mt-5">

                <label className="mb-2 block text-sm font-medium">
                  Outcome
                </label>

                <select
                  value={outcome}
                  onChange={(e) =>
                    setOutcome(e.target.value)
                  }
                  className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none"
                >

                  <option>
                    Resolved
                  </option>

                  <option>
                    Partially Resolved
                  </option>

                  <option>
                    Escalated
                  </option>

                  <option>
                    Under Investigation
                  </option>

                </select>

              </div>

              {/* FEEDBACK */}
              <div className="mt-5">

                <label className="mb-2 block text-sm font-medium">
                  Analyst Feedback
                </label>

                <textarea
                  value={feedback}
                  onChange={(e) =>
                    setFeedback(e.target.value)
                  }
                  placeholder="What should the AI remember for similar incidents in the future?"
                  rows={4}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-green-500"
                />

              </div>

              {/* SAVE */}
              <button
                onClick={saveExperience}
                disabled={saving}
                className="mt-6 rounded-lg bg-green-600 px-6 py-3 font-semibold transition hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving
                  ? "Saving to Hindsight..."
                  : "Save Experience to Hindsight"}
              </button>

              {/* SUCCESS */}
              {saved && (

                <div className="mt-5 rounded-lg border border-green-800 bg-green-950 p-4 text-green-300">

                  <p className="font-semibold">
                    ✅ Experience stored successfully!
                  </p>

                  <p className="mt-1 text-sm">
                    Hindsight can now use this experience
                    for future incidents.
                  </p>

                </div>

              )}

            </section>
          </>
        )}

      </div>
    </main>
  );
}