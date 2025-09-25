import { useEffect, useState } from "react";
import { JobsTable } from "./components/JobsTable";
import SourceToggle from "./components/SourceToggle";
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
    try {
      await fetch("http://localhost:8000/scrape", { method: "POST" });
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
    This app scrapes internship listings, highlights newly published offers, and makes them easy to explore.
  </p>

  <SourceToggle />

        <button
          onClick={handleScrape}
          disabled={loading}
          className={styles.scrapeButton}
        >
          {loading ? "Scraping..." : "Search"}
        </button>
      </div>

      {/* Content */}
      <div className={styles.content}>
        {jobs.length === 0 ? (
          <p className={styles.noJobsMessage}>
            Aucune offre disponible pour le moment.
          </p>
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

