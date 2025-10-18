import { useState } from "react";
import styles from "./JobsTable.module.css";

type Job = {
  company: string;
  title: string;
  location: string;
  link: string;
  new: boolean;
  module: string;
};

type Props = {
  jobs: Job[];
};

export function JobsTable({ jobs }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedModule, setSelectedModule] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const itemsPerPage = 10;

  // Extraire tous les modules uniques
  const modules = Array.from(new Set(jobs.map((job) => job.module)));

  // 🔍 Filtrer par module + terme de recherche
  const filteredJobs = jobs.filter((job) => {
    const matchesModule =
      selectedModule === "" || job.module === selectedModule;

    const search = searchTerm.trim().toLowerCase();
    const matchesSearch =
      search === "" ||
      Object.values(job).some((value) =>
        String(value).toLowerCase().includes(search)
      );

    return matchesModule && matchesSearch;
  });

  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const displayedJobs = filteredJobs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const emptyRows = itemsPerPage - displayedJobs.length;

  return (
    <div className={styles.container}>
      {/* FILTRES */}
      <div className={styles.filterContainer}>
        <label htmlFor="module-filter" className={styles.filterLabel}>
          Module :
        </label>
        <select
          id="module-filter"
          value={selectedModule}
          onChange={(e) => {
            setSelectedModule(e.target.value);
            setCurrentPage(1);
          }}
          className={styles.filterSelect}
        >
          <option value="">All</option>
          {modules.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        {/* 🔍 Barre de recherche */}
        <input
          type="text"
          placeholder="Search by title, company, location or link..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
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
          onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
          disabled={currentPage === 1}
          className={styles.paginationButton}
        >
          Previous
        </button>

        <span className={styles.paginationInfo}>
          {currentPage} / {totalPages || 1}
        </span>

        <button
          onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
          disabled={currentPage === totalPages || totalPages === 0}
          className={styles.paginationButton}
        >
          Next
        </button>
      </div>
    </div>
  );
}
