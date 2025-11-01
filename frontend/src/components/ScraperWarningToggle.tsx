import { useState } from "react";
import styles from "./SourceToggle.module.css";

export default function ScraperWarningToggle() {
  const [open, setOpen] = useState(false);

  return (
    <div className={styles.sourcesContainer}>
      <h2
        className={styles.sourcesTitle}
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer" }}
      >
        Issues and Improvements {open ? "▲" : "▼"}
      </h2>
      {open && (
        <p className={styles.sourcesText}>
          ⚠ Some scrapers may fail or miss certain job listings due to site
          changes. <br /> If you encounter any issues or have suggestions for
          improvements, please report them on{" "}
          <a
            href="https://github.com/NassAbd/InternApp/issues"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.sourceLink}
          >
            GitHub Issues
          </a>
          .
        </p>
      )}
    </div>
  );
}
