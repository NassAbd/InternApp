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

  useEffect(() => {
    fetchJobs();
  }, []);

  // Déclencher le scraping
  const handleScrape = async () => {
    setLoading(true);
    setFailedScrapers([]);
    try {
      const res = await fetch("http://localhost:8000/scrape", { method: "POST" });
      const data = await res.json();
      if (data.failed_scrapers && data.failed_scrapers.length > 0) {
        setFailedScrapers(data.failed_scrapers);
      }
      // Recharger les jobs après le scraping
      await fetchJobs();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
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

        <button
          onClick={handleScrape}
          disabled={loading}
          className={styles.scrapeButton}
        >
          {loading ? "Scraping..." : "Scrape"}
        </button>

        {/* Affichage des scrapers échoués */}
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
          <p>Go get a coffee, scraping all these sources will take a while...</p>
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
