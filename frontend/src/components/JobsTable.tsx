import styles from "./JobsTable.module.css";

type Job = {
  company: string;
  title: string;
  location: string;
  link: string;
  new: boolean;
  module: string;
  tags?: string[];
  match_score?: number;
  matching_tags?: string[];
};

type JobsData = {
  jobs: Job[];
  page: number;
  size: number;
  total_items: number;
  total_pages: number;
};

type Filters = {
  page: number;
  size: number;
  searchTerm: string;
  selectedModule: string;
};

type Props = {
  jobsData: JobsData;
  availableModules: string[];
  filters: Filters;
  onFilterChange: (newFilters: Partial<Filters>) => void;
  pendingSearchTerm: string;
  onPendingSearchChange: (term: string) => void;
  onSearchClick: () => void;
  isPersonalizedFeed?: boolean;
};

export function JobsTable({ jobsData, availableModules, filters, onFilterChange, pendingSearchTerm, onPendingSearchChange, onSearchClick, isPersonalizedFeed = false }: Props) {

  const { page, size, total_pages, total_items, jobs: displayedJobs } = jobsData;
  const { selectedModule } = filters;

  const handleModuleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ selectedModule: e.target.value });
  };

  // Calculate empty rows for table stability
  const emptyRows = size - displayedJobs.length;

  // Helper function to render tags with highlighting
  const renderTags = (job: Job) => {
    if (!job.tags || job.tags.length === 0) return null;

    return (
      <div className={styles.tagsContainer}>
        {job.tags.slice(0, 3).map((tag) => {
          const isMatching = isPersonalizedFeed && job.matching_tags?.includes(tag);
          return (
            <span
              key={tag}
              className={`${styles.tag} ${isMatching ? styles.tagMatching : ''}`}
            >
              {tag}
            </span>
          );
        })}
        {job.tags.length > 3 && (
          <span className={styles.tagMore}>+{job.tags.length - 3}</span>
        )}
      </div>
    );
  };

  return (
    <div className={styles.container}>
      {/* FILTERS */}
      <div className={styles.filterContainer}>
        <label htmlFor="module-filter" className={styles.filterLabel}>
          Module ({total_items} results):
        </label>
        <select
          id="module-filter"
          value={selectedModule}
          onChange={handleModuleChange}
          className={styles.filterSelect}
        >
          <option value="">All</option>
          {availableModules.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        {/* Search input and button */}
        <input
          type="text"
          placeholder="Search by title, company, location or link..."
          value={pendingSearchTerm}
          onChange={(e) => onPendingSearchChange(e.target.value)}
          className={styles.searchInput}
        />
        <button
          onClick={onSearchClick}
          className={styles.searchButton}
          disabled={pendingSearchTerm === filters.searchTerm}
        >
          Search
        </button>
      </div>

      {/* TABLE */}
      <table className={styles.table}>
        <thead className={styles.tableHead}>
          <tr>
            <th className={styles.tableHeadCell}>Title</th>
            <th className={styles.tableHeadCell}>Company</th>
            <th className={styles.tableHeadCell}>Location</th>
            {isPersonalizedFeed && (
              <th className={styles.tableHeadCell}>Match Score</th>
            )}
            <th className={styles.tableHeadCell}>Link</th>
          </tr>
        </thead>
        <tbody>
          {displayedJobs.map((job) => (
            <tr
              key={job.link}
              className={`${styles.tableRow} ${job.new ? styles.tableRowNew : ""
                } ${isPersonalizedFeed && job.match_score && job.match_score >= 15 ? styles.tableRowHighScore : ""
                }`}
            >
              <td className={styles.tableCell}>
                <div className={styles.titleContainer}>
                  <div className={styles.titleText}>{job.title}</div>
                  {renderTags(job)}
                </div>
              </td>
              <td className={styles.tableCell}>{job.company}</td>
              <td className={styles.tableCell}>{job.location}</td>
              {isPersonalizedFeed && (
                <td className={styles.tableCell}>
                  {job.match_score && (
                    <span className={`${styles.matchScore} ${job.match_score >= 15 ? styles.matchScoreHigh :
                      job.match_score >= 10 ? styles.matchScoreMedium :
                        styles.matchScoreLow
                      }`}>
                      {job.match_score}
                    </span>
                  )}
                </td>
              )}
              <td className={styles.tableCell}>
                <a
                  href={job.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.linkCell}
                >
                  See offer
                </a>
              </td>
            </tr>
          ))}

          {/* Empty rows */}
          {total_items > 0 && Array.from({ length: emptyRows }).map((_, idx) => (
            <tr key={`empty-${idx}`} style={{ height: "53px" }}>
              <td className={styles.tableCell}>&nbsp;</td>
              <td className={styles.tableCell}>&nbsp;</td>
              <td className={styles.tableCell}>&nbsp;</td>
              {isPersonalizedFeed && <td className={styles.tableCell}>&nbsp;</td>}
              <td className={styles.tableCell}>&nbsp;</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* PAGINATION */}
      <div className={styles.paginationContainer}>
        <button
          onClick={() => onFilterChange({ page: page - 1 })}
          disabled={page <= 1}
          className={styles.paginationButton}
        >
          Previous
        </button>

        <span className={styles.paginationInfo}>
          {page} / {total_pages || 1}
        </span>

        <button
          onClick={() => onFilterChange({ page: page + 1 })}
          disabled={page >= total_pages || total_pages === 0}
          className={styles.paginationButton}
        >
          Next
        </button>
      </div>
    </div>
  );
}
