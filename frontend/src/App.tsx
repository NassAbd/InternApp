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
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Internships</h1>

      <button
        onClick={handleScrape}
        className="px-4 py-2 bg-blue-600 text-white rounded mb-4"
        disabled={loading}
      >
        {loading ? "Scraping..." : "Rechercher"}
      </button>

      {jobs.length === 0 ? (
  <p className="text-gray-500 italic">
    Aucune offre disponible pour le moment.
  </p>
) : (
  <JobsTable jobs={jobs} />
)}
    </div>
  );
}

export default App;

