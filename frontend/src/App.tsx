import { useCallback, useEffect, useState } from "react";
import { JobsTable, FeedToggle, ProfileManager, CVUploader, ApplicationDashboard } from "./components";
import SourceToggle from "./components/SourceToggle";
import ScraperWarningToggle, { type FailedScraper } from "./components/ScraperWarningToggle";
import NotificationContainer from "./components/NotificationContainer";
import { NotificationProvider } from "./contexts/NotificationContext";
import { useApplicationTracker } from "./hooks/useApplicationTracker";
import { useNotifications } from "./contexts/NotificationContext";
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

type CurrentView = 'feed' | 'dashboard';

// Create a separate component that uses the hooks inside the provider
function AppContent() {
  const [currentView, setCurrentView] = useState<CurrentView>('feed');
  const [jobsData, setJobsData] = useState<JobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingState, setLoadingState] = useState<'idle' | 'scraping' | 'fetching' | 'analyzing'>('idle');
  const [failedScrapers, setFailedScrapers] = useState<(string | FailedScraper)[]>([]);
  const [selectedModules, setSelectedModules] = useState<string[]>([]);
  const [selectedFeed, setSelectedFeed] = useState<FeedType>("all");

  // List of all available modules for scraping
  const [availableScrapeModules, setAvailableScrapeModules] = useState<string[]>([]);

  const [filterableModules, setFilterableModules] = useState<string[]>([]);
  const [hasScraped, setHasScraped] = useState(false);

  const { addNotification } = useNotifications();
  

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

  // Application tracking - now inside the provider
  const applicationTracker = useApplicationTracker();


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
    setLoadingState('fetching');
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
      setLoadingState('idle');
    }
  }, [filters, isFilterActive, selectedFeed]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Load all available modules on mount
  useEffect(() => {
    fetchAvailableScrapeModules();
  }, []);

  // Handle URL-based routing
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1); // Remove the '#'
      if (hash === 'dashboard') {
        setCurrentView('dashboard');
      } else {
        setCurrentView('feed');
      }
    };

    // Set initial view based on current hash
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
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

  const navigateToFeed = () => {
    window.location.hash = '';
    setCurrentView('feed');
  };

  const navigateToDashboard = () => {
    window.location.hash = 'dashboard';
    setCurrentView('dashboard');
  };

  const handleScrape = async () => {
    setLoading(true);
    setLoadingState('scraping');
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
        addNotification({
          type: 'error',
          title: 'Scraping Request Failed',
          message: 'Some modules failed to scrape. Check the failed scrapers list for details.',
          duration: 5000,
        });
      }
      setFilters((prev) => ({ ...prev, page: 1 }));
      await fetchJobs();
      setHasScraped(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setLoadingState('idle');
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

  // Handle profile update success
  const handleProfileUpdate = () => {
    // Refresh jobs if we're on the personalized feed
    if (selectedFeed === "for-you") {
      fetchJobs();
    }
  };

  // Handle CV analysis state
  const handleCVAnalysisStart = () => {
    setLoadingState('analyzing');
  };

  const handleCVAnalysisEnd = () => {
    setLoadingState('idle');
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

  // Build a derived tracked set that includes both backend IDs and frontend IDs (btoa(link))
  const derivedTrackedJobs: Set<string> = (() => {
    const s = new Set<string>(applicationTracker.state.trackedJobs);
    try {
      for (const app of applicationTracker.state.applications) {
        try {
          const btoaId = btoa(app.job.link).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
          s.add(btoaId);
        } catch (_) {
          // ignore encoding issues
        }
      }
    } catch (_) {
      // ignore
    }
    return s;
  })();

  // Also build a set of tracked links for strict matching
  const trackedLinks: Set<string> = (() => {
    const s = new Set<string>();
    try {
      for (const app of applicationTracker.state.applications) {
        if (app.job?.link) s.add(app.job.link);
      }
    } catch (_) {
      // ignore
    }
    return s;
  })();

  // Map a possibly-frontend identifier to backend id before untracking.
  // Accepts either: exact job link, or btoa(link) short id, or backend id.
  const onUntrackJobProxy = async (inputId: string) => {
    let backendId = inputId;
    try {
      // 1) Try exact link equality first (collision-free)
      let match = applicationTracker.state.applications.find(app => app.job?.link === inputId);
      if (!match) {
        // 2) Fallback to btoa-derived id comparison
        match = applicationTracker.state.applications.find(app => {
          try {
            const derived = btoa(app.job.link).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
            return derived === inputId;
          } catch {
            return false;
          }
        });
      }
      if (match) backendId = match.id;
    } catch (_) {
      // ignore mapping failures and try with provided id
    }
    await applicationTracker.untrackJob(backendId);
  };

  // Handle overlay background click
  const handleOverlayClick = (e: React.MouseEvent, closeFunction: () => void) => {
    if (e.target === e.currentTarget) {
      closeFunction();
    }
  };

  return (
      <div className={styles.container}>
        <NotificationContainer />

        {/* Navigation */}
        <div className={styles.navigation}>
          <button
            onClick={navigateToFeed}
            className={`${styles.navButton} ${currentView === 'feed' ? styles.navButtonActive : ''}`}
          >
            Job Feed
          </button>
          <button
            onClick={navigateToDashboard}
            className={`${styles.navButton} ${currentView === 'dashboard' ? styles.navButtonActive : ''}`}
          >
            Dashboard
          </button>
        </div>

        {currentView === 'dashboard' ? (
          <ApplicationDashboard />
        ) : (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>Internships</h1>
              <p className={styles.subtitle}>
                Scrapes internship listings, highlights newly published offers, and makes them easy to explore.
              </p>

              <SourceToggle />
              <ScraperWarningToggle failedScrapers={failedScrapers} />

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
                {loadingState === 'scraping' ? "Scraping..." : "Scrape"}
              </button>

              {/* Profile Management Buttons */}
              <div className={styles.profileButtons}>
                <button
                  onClick={() => setShowProfileManager(true)}
                  className={styles.profileButton}
                >
                  Manage Profile
                </button>
                <button
                  onClick={() => setShowCVUploader(true)}
                  className={styles.cvButton}
                >
                  Upload CV
                </button>
              </div>
            </div>

            <div className={styles.content}>
              {loadingState === 'scraping' ? (
                <>
                  <div className={styles.loader}></div>
                  <p>Go get a tea, scraping these sources will take a while...</p>
                </>
              ) : loadingState === 'fetching' ? (
                <div className={styles.fetchingLoader}>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill}></div>
                  </div>
                  <p>Updating feed...</p>
                </div>
              ) : loading || !jobsData ? (
                <>
                  <div className={styles.loader}></div>
                  <p>Loading...</p>
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
                    trackedJobs={derivedTrackedJobs}
                    trackedLinks={trackedLinks}
                    onTrackJob={applicationTracker.trackJob}
                    onUntrackJob={onUntrackJobProxy}
                    trackingLoading={applicationTracker.state.loading}
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
          </>
        )}

        {/* Profile Manager Overlay */}
        {showProfileManager && (
          <div
            className={styles.overlay}
            onClick={(e) => handleOverlayClick(e, () => setShowProfileManager(false))}
          >
            <div className={styles.overlayContent}>
              <ProfileManager
                onClose={() => setShowProfileManager(false)}
                onProfileUpdate={handleProfileUpdate}
              />
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
                onAnalysisStart={handleCVAnalysisStart}
                onAnalysisEnd={handleCVAnalysisEnd}
              />
            </div>
          </div>
        )}
      </div>
  );
}

function App() {
  return (
    <NotificationProvider>
      <AppContent />
    </NotificationProvider>
  );
}

export default App;
