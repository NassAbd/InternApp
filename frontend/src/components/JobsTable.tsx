import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Job = {
  company: string;
  title: string;
  location: string;
  link: string;
  new: boolean;
  module: string; // <-- ajouté
};

type Props = {
  jobs: Job[];
};

export function JobsTable({ jobs }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedModule, setSelectedModule] = useState<string>("");

  const itemsPerPage = 10;

  // Extraire tous les modules uniques
  const modules = Array.from(new Set(jobs.map((job) => job.module)));

  // Appliquer filtre si un module est sélectionné
  const filteredJobs =
    selectedModule === ""
      ? jobs
      : jobs.filter((job) => job.module === selectedModule);

  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const displayedJobs = filteredJobs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const emptyRows = itemsPerPage - displayedJobs.length;

  return (
    <div className="overflow-auto border rounded shadow-sm max-h-[500px] p-4 space-y-4">
      {/* FILTRE */}
      <div
  style={{
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  }}
>
  <label
    htmlFor="module-filter"
    style={{
      fontWeight: 500, // équivalent Tailwind "font-medium"
    }}
  >
    Module :
  </label>

  <select
    id="module-filter"
    value={selectedModule}
    onChange={(e) => {
      setSelectedModule(e.target.value);
      setCurrentPage(1); // reset pagination au changement de filtre
    }}
    style={{
      border: "1px solid #d1d5db", // gris clair (tailwind gray-300 approx)
      borderRadius: "0.25rem",
      padding: "0.25rem 0.5rem",
    }}
  >
    <option value="">All</option>
    {modules.map((m) => (
      <option key={m} value={m}>
        {m}
      </option>
    ))}
  </select>
</div>


      {/* TABLE */}
      <Table className="table-fixed w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="w-1/4">Title</TableHead>
            <TableHead className="w-1/4">Company</TableHead>
            <TableHead className="w-1/4">Location</TableHead>
            <TableHead className="w-1/6">Link</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayedJobs.map((job) => (
            <TableRow
            key={job.link}
            style={{
              backgroundColor: job.new ? "#DCFCE7" : "transparent",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = job.new ? "#BBF7D0" : "#F3F4F6";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = job.new ? "#DCFCE7" : "transparent";
            }}
          >
              <TableCell
                className="truncate"
              >
                {job.title}
              </TableCell>
              <TableCell
                className="truncate"
              >
                {job.company}
              </TableCell>
              <TableCell
                className="truncate"
              >
                {job.location}
              </TableCell>
              <TableCell
                className="truncate"
              >
                <a
                  href={job.link}
                  target="_blank"
                  className="text-blue-500 underline"
                >
                  See offer
                </a>
              </TableCell>
            </TableRow>
          ))}

          {/* Lignes fantômes */}
          {Array.from({ length: emptyRows }).map((_, idx) => (
            <TableRow key={`empty-${idx}`} className="h-10">
              <TableCell>&nbsp;</TableCell>
              <TableCell>&nbsp;</TableCell>
              <TableCell>&nbsp;</TableCell>
              <TableCell>&nbsp;</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* PAGINATION */}
      <div
  style={{
    display: "flex",
    justifyContent: "center",
    gap: "0.5rem",
    marginTop: "1rem",
  }}
>
  <button
    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
    disabled={currentPage === 1}
    style={{
      padding: "0.25rem 0.75rem",
      backgroundColor: "#e5e7eb", // gray-200
      borderRadius: "0.375rem",
      opacity: currentPage === 1 ? 0.5 : 1,
      cursor: currentPage === 1 ? "not-allowed" : "pointer",
    }}
  >
    Previous
  </button>

  <span
    style={{
      padding: "0.25rem 0.75rem",
      display: "inline-block",
    }}
  >
    {currentPage} / {totalPages || 1}
  </span>

  <button
    onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
    disabled={currentPage === totalPages || totalPages === 0}
    style={{
      padding: "0.25rem 0.75rem",
      backgroundColor: "#e5e7eb", // gray-200
      borderRadius: "0.375rem",
      opacity: currentPage === totalPages || totalPages === 0 ? 0.5 : 1,
      cursor:
        currentPage === totalPages || totalPages === 0
          ? "not-allowed"
          : "pointer",
    }}
  >
    Next
  </button>
</div>

    </div>
  );
}
