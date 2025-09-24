import { useEffect, useState } from "react";
import { JobsTable } from "./components/JobsTable";

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
    <div
  style={{
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "1.5rem",
    height: "100vh", // prend toute la page
    boxSizing: "border-box",
  }}
>
  {/* Header : titre + bouton */}
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      marginBottom: "1.5rem",
    }}
  >
    <h1
      style={{
        fontSize: "2.5rem",
        fontWeight: "bold",
        marginBottom: "1rem",
      }}
    >
      Internships
    </h1>

    <button
      onClick={handleScrape}
      disabled={loading}
      style={{
        padding: "1rem 2rem",
        backgroundColor: "#86EFAC",
        color: "#065F46",
        border: "none",
        borderRadius: "0.5rem",
        fontSize: "1.25rem",
        fontWeight: 600,
        cursor: loading ? "not-allowed" : "pointer",
        opacity: loading ? 0.7 : 1,
        transition: "background-color 0.2s ease",
      }}
      onMouseEnter={(e) => {
        if (!loading) e.currentTarget.style.backgroundColor = "#4ADE80";
      }}
      onMouseLeave={(e) => {
        if (!loading) e.currentTarget.style.backgroundColor = "#86EFAC";
      }}
    >
      {loading ? "Scraping..." : "Search"}
    </button>
  </div>

  {/* Content */}
  <div
    style={{
      flex: 1, // prend tout l’espace restant
      width: "100%",
      maxWidth: "1200px",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    }}
  >
    {jobs.length === 0 ? (
      <p
        style={{
          color: "#6B7280",
          fontStyle: "italic",
          marginTop: "2rem",
        }}
      >
        Aucune offre disponible pour le moment.
      </p>
    ) : (
      <div
        style={{
          width: "100%",
          height: "100%", // prend tout l'espace restant
          overflowY: "auto", // scroll interne si besoin
        }}
      >
        <JobsTable jobs={jobs} />
      </div>
    )}
  </div>
</div>


  );
}

export default App;

