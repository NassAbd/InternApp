import styles from "./JobsTable.module.css";

type Job = {
  company: string;
  title: string;
  location: string;
  link: string;
  new: boolean;
  module: string;
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
  filters: Filters;
  onFilterChange: (newFilters: Partial<Filters>) => void;
  availableModules: string[];
};

export function JobsTable({
  jobsData,
  filters,
  onFilterChange,
  availableModules,
}: Props) {
  const { jobs: displayedJobs, page, size, total_pages } = jobsData;
  const emptyRows = size - displayedJobs.length;

  return (
    <div className={styles.container}>
      {/* FILTRES */}
      <div className={styles.filterContainer}>
        <label htmlFor="module-filter" className={styles.filterLabel}>
          Module :
        </label>
        <select
          id="module-filter"
          value={filters.selectedModule}
          onChange={(e) =>
            onFilterChange({ selectedModule: e.target.value, page: 1 })
          }
          className={styles.filterSelect}
        >
          <option value="">All</option>
          {availableModules.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        {/* 🔍 Barre de recherche */}
        <input
          type="text"
          placeholder="Search by title, company, location or link..."
          value={filters.searchTerm}
          onChange={(e) =>
            onFilterChange({ searchTerm: e.target.value, page: 1 })
          }
          className={styles.searchInput}
        />
      </div>

      {/* TABLE */}
      <table className={styles.table}>
        <thead className={styles.tableHead}>
          <tr>
            <th className={styles.tableHeadCell}>Title</th>
            <th className={styles.tableHeadCell}>Company</th>
            <th className={styles.tableHeadCell}>Location</th>
            <th className={styles.tableHeadCell}>Link</th>
          </tr>
        </thead>
        <tbody>
          {displayedJobs.map((job) => (
            <tr
              key={job.link}
              className={`${styles.tableRow} ${
                job.new ? styles.tableRowNew : ""
              }`}
            >
              <td className={styles.tableCell}>{job.title}</td>
              <td className={styles.tableCell}>{job.company}</td>
              <td className={styles.tableCell}>{job.location}</td>
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

          {/* Lignes fantômes */}
          {Array.from({ length: emptyRows }).map((_, idx) => (
            <tr key={`empty-${idx}`} style={{ height: "53px" }}>
              <td className={styles.tableCell}>&nbsp;</td>
              <td className={styles.tableCell}>&nbsp;</td>
              <td className={styles.tableCell}>&nbsp;</td>
              <td className={styles.tableCell}>&nbsp;</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* PAGINATION */}
      <div className={styles.paginationContainer}>
        <button
          onClick={() => onFilterChange({ page: page - 1 })}
          disabled={page === 1}
          className={styles.paginationButton}
        >
          Previous
        </button>

        <span className={styles.paginationInfo}>
          {page} / {total_pages || 1}
        </span>

        <button
          onClick={() => onFilterChange({ page: page + 1 })}
          disabled={page === total_pages || total_pages === 0}
          className={styles.paginationButton}
        >
          Next
        </button>
      </div>
    </div>
  );
}
