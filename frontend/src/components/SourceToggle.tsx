import { useState } from "react";
import styles from "./SourceToggle.module.css";

export default function SourceToggle() {
  const [open, setOpen] = useState(false);
  const sources = [
    { name: "Airbus", url: "https://ag.wd3.myworkdayjobs.com/fr-FR/Airbus?workerSubType=f5811cef9cb50193723ed01d470a6e15&locationCountry=54c5b6971ffb4bf0b116fe7651ec789a" },
    { name: "Ariane group", url: "https://arianegroup.wd3.myworkdayjobs.com/fr-FR/EXTERNALALL?q=stage+&workerSubType=a18ef726d66501f47d72e293b31c2c27" },
    { name: "Ariane talent", url: "https://talent.arianespace.com/jobs" },
    { name: "CNES", url: "https://recrutement.cnes.fr/fr/annonces?contractTypes=3" },
    { name: "Thales", url: "https://careers.thalesgroup.com/fr/fr/search-results?keywords=stage" },
  ];

  return (
    <div className={styles.sourcesContainer}>
      <h2
        className={styles.sourcesTitle}
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer" }}
      >
        Scrapers Sources {open ? "▲" : "▼"}
      </h2>
      {open && (
        <p className={styles.sourcesText}>
          {sources.map((source, index) => (
            <span key={source.name}>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.sourceLink}
              >
                {source.name}
              </a>
              {index < sources.length - 1 && ", "}
            </span>
          ))}
        </p>
      )}
    </div>
  );
}
