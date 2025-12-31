import { useCallback, useEffect, useState } from "react";
import { JobsTable, FeedToggle, ProfileManager, CVUploader } from "./components";
import SourceToggle from "./components/SourceToggle";
import ScraperWarningToggle from "./components/ScraperWarningToggle";
import styles from "./App.module.css";
import type { FeedType } from "./components/FeedToggle";

type Job = {
  id: number;
  company: string;
  title: string;
  location: string;
  link: string;
  module: string;
  new: boolean;
  tags?: string[];
  match_score?: number;
  matching_tags?: string[];
};

type JobsResponse = {
  jobs: Job[];
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
  filterable_modules: string[];
};

function App() {
  const [jobsData, setJobsData] = useState<JobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failedScrapers, setFailedScrapers] = useState<string[]>([]);
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [selectedFeed, setSelectedFeed] = useState<FeedType>("all");

  // List of all available modules for scraping
  const [availableScrapeModules, setAvailableScrapeModules] = useState<string[]>([]);

  const [filterableModules, setFilterableModules] = useState<string[]>([]);
  const [hasScraped, setHasScraped] = useState(false);

  const [filters, setFilters] = useState({
    page: 1,
    size: 10,
    searchTerm: "",
    selectedModule: "",
  });

  // Temporary search term, not linked to the automatic API request.
  const [pendingSearchTerm, setPendingSearchTerm] = useState(filters.searchTerm);

  // Overlay states
  const [showProfileManager, setShowProfileManager] = useState(false);
  const [showCVUploader, setShowCVUploader] = useState(false);


  const isFilterActive = filters.searchTerm !== "" || filters.selectedModule !== "";

  const fetchAvailableScrapeModules = async () => {
    try {
      const res = await fetch("http://localhost:8000/modules");
      const data = await res.json();
      setAvailableScrapeModules(data);
    } catch (err) {
      console.error("Error fetching all scrape modules:", err);
      setAvailableScrapeModules([]);
    }
  };

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      page: String(filters.page),
      size: String(filters.size),
    });

    if (filters.selectedModule) {
      params.append("modules", filters.selectedModule);
    }
    if (filters.searchTerm) {
      params.append("search", filters.searchTerm);
    }

    try {
      const endpoint = selectedFeed === "for-you" ?
        `http://localhost:8000/jobs/for-you?${params.toString()}` :
        `http://localhost:8000/jobs?${params.toString()}`;

      const res = await fetch(endpoint);
      const data: JobsResponse = await res.json();
      setJobsData(data);
      setFilterableModules(data.filterable_modules || []);

      if (data.total_items > 0 && !isFilterActive) {
        setHasScraped(true);
      }
    } catch (err) {
      setJobsData(null);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters, isFilterActive, selectedFeed]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Load all available modules on mount
  useEffect(() => {
    fetchAvailableScrapeModules();
  }, []);

  // Synchronise the temporary search term when the real filter changes (e.g: reset).
  useEffect(() => {
    setPendingSearchTerm(filters.searchTerm);
  }, [filters.searchTerm]);


  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    if (newFilters.selectedModule !== undefined || newFilters.page !== undefined) {
      setFilters((prev) => ({
        ...prev,
        ...newFilters,
        // Reset page to 1 if module is selected, otherwise keep the current page.
        page: newFilters.selectedModule !== undefined ? 1 : (newFilters.page || prev.page)
      }));
    } else {
      setFilters((prev) => ({ ...prev, ...newFilters }));
    }
  };

  const handleSearchClick = () => {
    // Update the real filter and reset page to 1 for the new search.
    // It will trigger fetchJobs via the useEffect principal.
    setFilters((prev) => ({
      ...prev,
      searchTerm: pendingSearchTerm,
      page: 1,
    }));
  };

  const handleFeedChange = (feed: FeedType) => {
    setSelectedFeed(feed);
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

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
      setFilters((prev) => ({ ...prev, page: 1 }));
      await fetchJobs();
      setHasScraped(true);
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

  const isDatabaseEmpty = !hasScraped && !isFilterActive;
  const isFilteredButEmpty = jobsData?.total_items === 0 && isFilterActive;

  // Handle CV upload success
  const handleCVUploadSuccess = () => {
    setShowCVUploader(false);
    // Refresh jobs if we're on the personalized feed
    if (selectedFeed === "for-you") {
      fetchJobs();
    }
  };

  // Handle overlay close with ESC key
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowProfileManager(false);
        setShowCVUploader(false);
      }
    };

    if (showProfileManager || showCVUploader) {
      document.addEventListener('keydown', handleEscKey);
      // Prevent body scroll when overlay is open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'unset';
    };
  }, [showProfileManager, showCVUploader]);

  // Handle overlay background click
  const handleOverlayClick = (e: React.MouseEvent, closeFunction: () => void) => {
    if (e.target === e.currentTarget) {
      closeFunction();
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Internships</h1>
        <p className={styles.subtitle}>
          Scrapes internship listings, highlights newly published offers, and makes them easy to explore.
        </p>

        <SourceToggle />
        <ScraperWarningToggle />

        <p className={styles.warning}>⚠ Scrape all these modules can take a while. You can select specific modules to scrape if you want to save time.</p>

        <div className={styles.modulesContainer}>
          {availableScrapeModules.length === 0 ? (
            <p>Loading modules...</p>
          ) : (
            availableScrapeModules.map((m) => (
              <label key={m} className={styles.moduleCheckbox}>
                <input
                  type="checkbox"
                  value={m}
                  checked={selectedModules.includes(m)}
                  onChange={() => toggleModule(m)}
                  className={styles.hiddenCheckbox}
                />
                <span className={styles.moduleLabelText}>{m}</span>
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

        {/* Profile Management Buttons */}
        <div className={styles.profileButtons}>
          <button
            onClick={() => setShowProfileManager(true)}
            className={styles.profileButton}
          >
            📋 Manage Profile
          </button>
          <button
            onClick={() => setShowCVUploader(true)}
            className={styles.cvButton}
          >
            📄 Upload CV
          </button>
        </div>

        {failedScrapers.length > 0 && (
          <p className={styles.failedScrapers}>
            ⚠ Scrapers failed: {failedScrapers.join(", ")}
          </p>
        )}
      </div>

      <div className={styles.content}>
        {loading || !jobsData ? (
          <>
            <div className={styles.loader}></div>
            <p>Go get a tea, scraping these sources will take a while...</p>
          </>
        ) : (
          <div className={styles.jobsContainer}>
            <FeedToggle
              selectedFeed={selectedFeed}
              onFeedChange={handleFeedChange}
              hasPersonalizedResults={jobsData?.total_items ? jobsData.total_items > 0 : false}
            />

            <JobsTable
              jobsData={jobsData}
              filters={filters}
              onFilterChange={handleFilterChange}
              availableModules={filterableModules}
              pendingSearchTerm={pendingSearchTerm}
              onPendingSearchChange={setPendingSearchTerm}
              onSearchClick={handleSearchClick}
              isPersonalizedFeed={selectedFeed === "for-you"}
            />

            {isDatabaseEmpty && (
              <p className={styles.noJobsMessage}>
                No jobs scraped yet. Click 'Scrape'...
              </p>
            )}

            {isFilteredButEmpty && (
              <p className={styles.noJobsMessage}>
                No jobs match your current search criteria...
              </p>
            )}
          </div>
        )}
      </div>

      {/* Profile Manager Overlay */}
      {showProfileManager && (
        <div
          className={styles.overlay}
          onClick={(e) => handleOverlayClick(e, () => setShowProfileManager(false))}
        >
          <div className={styles.overlayContent}>
            <ProfileManager onClose={() => setShowProfileManager(false)} />
          </div>
        </div>
      )}

      {/* CV Uploader Overlay */}
      {showCVUploader && (
        <div
          className={styles.overlay}
          onClick={(e) => handleOverlayClick(e, () => setShowCVUploader(false))}
        >
          <div className={styles.overlayContent}>
            <CVUploader
              onUploadSuccess={handleCVUploadSuccess}
              onClose={() => setShowCVUploader(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
