import { useState } from "react"; // <--- Obligatoire
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
};

type Props = {
  jobs: Job[];
};

export function JobsTable({ jobs }: Props) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const totalPages = Math.ceil(jobs.length / itemsPerPage);
  const displayedJobs = jobs.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Calcul du nombre de lignes "fantômes" à ajouter pour garder la hauteur
  const emptyRows = itemsPerPage - displayedJobs.length;

  return (
    <div className="overflow-auto border rounded shadow-sm max-h-[500px]">
      <Table className="table-fixed w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="w-1/3">Titre</TableHead>
            <TableHead className="w-1/4">Entreprise</TableHead>
            <TableHead className="w-1/4">Lieu</TableHead>
            <TableHead className="w-1/6">Lien</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayedJobs.map((job) => (
            <TableRow key={job.link}>
  <TableCell
  className="truncate"
  style={job.new ? { backgroundColor: "#DCFCE7" } : undefined}
>
  {job.title}
</TableCell>
  <TableCell
  className="truncate"
  style={job.new ? { backgroundColor: "#DCFCE7" } : undefined}
>
  {job.company}
</TableCell>
  <TableCell
  className="truncate"
  style={job.new ? { backgroundColor: "#DCFCE7" } : undefined}
>
  {job.location}
</TableCell>
  <TableCell
  className="truncate"
  style={job.new ? { backgroundColor: "#DCFCE7" } : undefined}
>
    <a
      href={job.link}
      target="_blank"
      className="text-blue-500 underline"
    >
      Voir l'offre
    </a>
  </TableCell>
</TableRow>
          ))}

          {/* Lignes vides pour conserver la hauteur */}
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

      {/* Pagination */}
      <div className="flex justify-center gap-2 mt-4">
        <button
          onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Précédent
        </button>

        <span className="px-3 py-1">
          {currentPage} / {totalPages}
        </span>

        <button
          onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
          disabled={currentPage === totalPages}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Suivant
        </button>
      </div>
    </div>
  );
}
