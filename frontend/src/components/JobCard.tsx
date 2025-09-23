type Props = {
  jobs: Job[];
};

export function JobCard({ jobs }: Props) {
  return (
    <div className="grid gap-4">
      {jobs.map((job) => (
        <div key={job.id} className="p-4 border rounded-2xl shadow-md">
          <h2 className="text-lg font-semibold">{job.title}</h2>
          <p className="text-sm">{job.company} — {job.location}</p>
          <a href={job.link} target="_blank" className="text-blue-500 underline text-sm">
            Voir l'offre
          </a>
        </div>
      ))}
    </div>
  );
}
