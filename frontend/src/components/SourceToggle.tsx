import { useState } from "react";
import styles from "./SourceToggle.module.css";

export default function SourceToggle() {
  const [open, setOpen] = useState(false); // fermé par défaut
  const sources = ["Ariane", "Safran"];

  return (
    <div className={styles.sourcesContainer}>
      <h2
        className={styles.sourcesTitle}
        onClick={() => setOpen(!open)}
        style={{ cursor: "pointer" }}
      >
        Sources {open ? "▲" : "▼"}
      </h2>
      {open && (
        <p className={styles.sourcesText}>
          {sources.join(", ")}
        </p>
      )}
    </div>
  );
}
