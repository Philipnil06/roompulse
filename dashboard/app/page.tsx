"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type Comfort = {
  label: string;
  issues: string[];
  message: string;
};

type Measurement = {
  id: number;
  temperature_c: number;
  humidity_pct: number;
  measured_at: string;
  age_seconds: number;
  stale: boolean;
  comfort: Comfort;
};

type MetricSummary = {
  min: number;
  max: number;
  average: number;
  change: number;
  trend: "rising" | "falling" | "stable";
};

type Summary = {
  sample_count: number;
  window_hours: number;
  temperature_c: MetricSummary;
  humidity_pct: MetricSummary;
};

type HistoryResponse = {
  measurements: Measurement[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";
const ROOM_ID = "room-philip";

const trendLabels = {
  rising: "Rising",
  falling: "Falling",
  stable: "Stable",
};

export default function Home() {
  const [latest, setLatest] = useState<Measurement | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [history, setHistory] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [latestResponse, summaryResponse, historyResponse] =
        await Promise.all([
          fetch(`${API_URL}/v1/rooms/${ROOM_ID}/latest`, { cache: "no-store" }),
          fetch(`${API_URL}/v1/rooms/${ROOM_ID}/summary?hours=24`, {
            cache: "no-store",
          }),
          fetch(`${API_URL}/v1/rooms/${ROOM_ID}/history?hours=24&limit=96`, {
            cache: "no-store",
          }),
        ]);

      if (![latestResponse, summaryResponse, historyResponse].every((r) => r.ok)) {
        throw new Error("The local API is reachable, but it has no room data yet.");
      }

      setLatest((await latestResponse.json()) as Measurement);
      setSummary((await summaryResponse.json()) as Summary);
      setHistory(
        ((await historyResponse.json()) as HistoryResponse).measurements,
      );
      setError(null);
      setLastRefresh(new Date());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not reach the RoomPulse API.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 30_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [refresh]);

  const bars = useMemo(() => history.slice(-36), [history]);
  const minTemp = Math.min(...bars.map((item) => item.temperature_c), 18);
  const maxTemp = Math.max(...bars.map((item) => item.temperature_c), 26);
  const tempSpan = Math.max(maxTemp - minTemp, 1);

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="RoomPulse home">
          <span className="brandMark" aria-hidden="true">
            <span />
          </span>
          <span>ROOMPULSE</span>
        </a>
        <div className="livePill">
          <span className={error ? "statusDot statusDotError" : "statusDot"} />
          {error ? "LOCAL DEMO" : "LIVE SENSOR"}
        </div>
      </header>

      <section className="hero" id="top">
        <div className="heroCopy">
          <p className="eyebrow">PHYSICAL DATA · GROUNDED AI</p>
          <h1>
            Your room,
            <br />
            now <em>queryable.</em>
          </h1>
          <p className="lede">
            Live climate telemetry from an Axiometa Genesis Mini — ready for
            Codex and ChatGPT to read, summarize, and explain.
          </p>
        </div>

        <div className="nowPanel">
          <div className="nowHeader">
            <span>RIGHT NOW</span>
            <span>
              {latest
                ? formatTime(latest.measured_at)
                : loading
                  ? "CONNECTING"
                  : "WAITING"}
            </span>
          </div>
          <div className="primaryReading">
            <span className="readingValue">
              {latest ? latest.temperature_c.toFixed(1) : "—"}
            </span>
            <span className="readingUnit">°C</span>
          </div>
          <div className="humidityRow">
            <span>RELATIVE HUMIDITY</span>
            <strong>
              {latest ? `${latest.humidity_pct.toFixed(1)}%` : "—"}
            </strong>
          </div>
          <div className="comfortRow">
            <span
              className={`comfortIcon ${
                latest?.comfort.label !== "comfortable" ? "comfortWarning" : ""
              }`}
              aria-hidden="true"
            >
              {latest?.comfort.label === "comfortable" ? "✓" : "!"}
            </span>
            <div>
              <strong>
                {latest
                  ? titleCase(latest.comfort.label)
                  : "Awaiting first measurement"}
              </strong>
              <p>
                {latest
                  ? latest.comfort.message
                  : "Start the API and send a sensor reading to begin."}
              </p>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <section className="notice" role="status">
          <div>
            <strong>No measurements yet</strong>
            <p>{error}</p>
          </div>
          <button type="button" onClick={() => void refresh()}>
            Try again
          </button>
        </section>
      )}

      <section className="metricsSection" aria-labelledby="trend-title">
        <div className="sectionHeading">
          <div>
            <p className="eyebrow">24 HOUR WINDOW</p>
            <h2 id="trend-title">The room has a rhythm.</h2>
          </div>
          <p>
            {summary
              ? `${summary.sample_count} grounded measurements`
              : "Waiting for grounded measurements"}
          </p>
        </div>

        <div className="metricsGrid">
          <article className="metricCard temperatureCard">
            <div className="metricTop">
              <span>TEMPERATURE</span>
              <strong>
                {summary
                  ? `${signed(summary.temperature_c.change)}°`
                  : "—"}
              </strong>
            </div>
            <div className="chart" aria-label="Temperature history chart">
              {bars.length > 0 ? (
                bars.map((item) => (
                  <span
                    key={item.id}
                    style={{
                      height: `${22 + ((item.temperature_c - minTemp) / tempSpan) * 72}%`,
                    }}
                    title={`${item.temperature_c.toFixed(1)} °C at ${formatTime(item.measured_at)}`}
                  />
                ))
              ) : (
                <div className="emptyChart">Sensor history will appear here</div>
              )}
            </div>
            <div className="rangeRow">
              <div>
                <span>LOW</span>
                <strong>
                  {summary ? `${summary.temperature_c.min.toFixed(1)}°` : "—"}
                </strong>
              </div>
              <div>
                <span>AVERAGE</span>
                <strong>
                  {summary
                    ? `${summary.temperature_c.average.toFixed(1)}°`
                    : "—"}
                </strong>
              </div>
              <div>
                <span>HIGH</span>
                <strong>
                  {summary ? `${summary.temperature_c.max.toFixed(1)}°` : "—"}
                </strong>
              </div>
            </div>
          </article>

          <article className="metricCard humidityCard">
            <div className="metricTop">
              <span>HUMIDITY</span>
              <strong>
                {summary
                  ? trendLabels[summary.humidity_pct.trend]
                  : "—"}
              </strong>
            </div>
            <div className="humidityGauge">
              <div className="gaugeLabels">
                <span>DRY</span>
                <span>IDEAL</span>
                <span>HUMID</span>
              </div>
              <div className="gaugeTrack">
                <span
                  style={{
                    left: `${Math.min(
                      100,
                      Math.max(0, latest?.humidity_pct ?? 0),
                    )}%`,
                  }}
                />
              </div>
              <div className="gaugeValue">
                {latest ? `${latest.humidity_pct.toFixed(0)}%` : "—"}
              </div>
            </div>
            <div className="rangeRow">
              <div>
                <span>LOW</span>
                <strong>
                  {summary ? `${summary.humidity_pct.min.toFixed(0)}%` : "—"}
                </strong>
              </div>
              <div>
                <span>AVERAGE</span>
                <strong>
                  {summary
                    ? `${summary.humidity_pct.average.toFixed(0)}%`
                    : "—"}
                </strong>
              </div>
              <div>
                <span>HIGH</span>
                <strong>
                  {summary ? `${summary.humidity_pct.max.toFixed(0)}%` : "—"}
                </strong>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="askSection">
        <div>
          <p className="eyebrow">ASK WITH CODEX OR CHATGPT</p>
          <h2>The numbers speak plain language.</h2>
        </div>
        <div className="promptList">
          <div>
            <span>01</span>
            <p>“Is my room comfortable right now?”</p>
          </div>
          <div>
            <span>02</span>
            <p>“When was it warmest today?”</p>
          </div>
          <div>
            <span>03</span>
            <p>“How has humidity changed since this morning?”</p>
          </div>
        </div>
      </section>

      <footer>
        <span>Axiometa Genesis Mini · DHT11 · FastAPI · MCP</span>
        <span>
          {lastRefresh
            ? `Dashboard refreshed ${lastRefresh.toLocaleTimeString("sv-SE", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}`
            : "Waiting for API"}
        </span>
      </footer>
    </main>
  );
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString("sv-SE", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
