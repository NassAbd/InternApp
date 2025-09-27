import { useEffect, useState } from "react";
import { JobsTable } from "./components/JobsTable";
import SourceToggle from "./components/SourceToggle";
import ScraperWarningToggle from "./components/ScraperWarningToggle";
import styles from "./App.module.css";

type Job = {
  id: number;
  company: string;
  title: string;
  location: string;
  link: string;
};

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [failedScrapers, setFailedScrapers] = useState<string[]>([]);
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [availableModules, setAvailableModules] = useState<string[]>([]);

  // Charger les jobs existants
  const fetchJobs = async () => {
    try {
      const res = await fetch("http://localhost:8000/jobs");
      const data = await res.json();
      setJobs(data);
    } catch {
      setJobs([]);
    }
  };

  // Charger la liste des modules
  const fetchModules = async () => {
    try {
      const res = await fetch("http://localhost:8000/modules");
      const data = await res.json();
      setAvailableModules(data);
    } catch {
      setAvailableModules([]);
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchModules();
  }, []);

  // Déclencher le scraping
  const handleScrape = async () => {
    setLoading(true);
    setFailedScrapers([]);
    try {
      const endpoint =
        selectedModules.length === 0
          ? "http://localhost:8000/scrape"
          : "http://localhost:8000/scrape_modules";

      const options =
        selectedModules.length === 0
          ? { method: "POST" }
          : {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ modules: selectedModules }),
            };

      const res = await fetch(endpoint, options);
      const data = await res.json();
      if (data.failed_scrapers && data.failed_scrapers.length > 0) {
        setFailedScrapers(data.failed_scrapers);
      }
      await fetchJobs();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleModule = (module: string) => {
    setSelectedModules((prev) =>
      prev.includes(module)
        ? prev.filter((m) => m !== module)
        : [...prev, module]
    );
  };

  return (
    <div className={styles.container}>
      {/* Header : titre + bouton */}
      <div className={styles.header}>
        <h1 className={styles.title}>Internships</h1>
        <p className={styles.subtitle}>
          Scrapes internship listings, highlights newly published offers, and makes them easy to explore.
        </p>

        <SourceToggle />
        <ScraperWarningToggle />

        {/* Sélecteur de modules (chargé dynamiquement) */}
        <div className={styles.modulesContainer}>
          {availableModules.length === 0 ? (
            <p>Loading modules...</p>
          ) : (
            availableModules.map((m) => (
              <label key={m} className={styles.moduleCheckbox}>
                <input
                  type="checkbox"
                  value={m}
                  checked={selectedModules.includes(m)}
                  onChange={() => toggleModule(m)}
                />
                {m}
              </label>
            ))
          )}
        </div>

        <button
          onClick={handleScrape}
          disabled={loading}
          className={styles.scrapeButton}
        >
          {loading ? "Scraping..." : "Scrape"}
        </button>

        {failedScrapers.length > 0 && (
          <p className={styles.failedScrapers}>
            ⚠ Scrapers failed: {failedScrapers.join(", ")}
          </p>
        )}
      </div>

      {/* Content */}
      <div className={styles.content}>
        {loading ? (
          <>
            <div className={styles.loader}></div>
            <p>Go get a tea, scraping these sources will take a while...</p>
          </>
        ) : jobs.length === 0 ? (
          <p className={styles.noJobsMessage}>No jobs scraped yet.</p>
        ) : (
          <div className={styles.jobsContainer}>
            <JobsTable jobs={jobs} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
