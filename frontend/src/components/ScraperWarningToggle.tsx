import { useState } from "react";
import styles from "./SourceToggle.module.css";

export interface Diagnosis {
  explanation: string;
  suggested_fix: string;
}

export interface FailedScraper {
  module: string;
  error: string;
  diagnosis?: Diagnosis | null;
}

export interface ScraperWarningToggleProps {
  failedScrapers?: (string | FailedScraper)[];
}

export default function ScraperWarningToggle({ failedScrapers = [] }: ScraperWarningToggleProps) {
  const [open, setOpen] = useState(false);

  // Normalize failed scrapers to object format
  const normalizedFailures: FailedScraper[] = failedScrapers.map(f => {
    if (typeof f === 'string') return { module: f, error: 'Unknown error', diagnosis: null };
    return f;
  });

  const hasFailures = normalizedFailures.length > 0;

  return (
    <div className={styles.sourcesContainer}>
      <h2
        className={styles.sourcesTitle}
        onClick={() => setOpen(!open)}
        style={{ 
          cursor: "pointer", 
          color: hasFailures ? '#ef4444' : undefined 
        }}
      >
        {/* Title is now fixed as requested */}
        Issues and Improvements {hasFailures && `(${normalizedFailures.length})`} {open ? "▲" : "▼"}
      </h2>
      
      {open && (
        <div className={styles.sourcesText} style={{ textAlign: 'left', maxWidth: '800px' }}>
          
          {/* 1. Permanent Part: Always displayed */}
          <p className={styles.sourcesContainer} style={{ marginBottom: hasFailures ? '1.5rem' : '0' }}>
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

          {/* 2. Failures Part: Displayed below only if hasFailures is true */}
          {hasFailures && (
            <div>
              <p style={{ fontWeight: 'bold', marginBottom: '0.5rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                The following scrapers encountered errors:
              </p>
              {normalizedFailures.map((failure, idx) => (
                <div key={idx} style={{ 
                  border: '1px solid #fee2e2', 
                  backgroundColor: '#fef2f2', 
                  borderRadius: '0.5rem', 
                  padding: '1rem',
                  marginBottom: '1rem' 
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0, color: '#b91c1c' }}>{failure.module}</h3>
                  </div>
                  
                  <p style={{ margin: '0.5rem 0', fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                    {failure.error}
                  </p>

                  {failure.diagnosis && (
                    <div style={{ marginTop: '1rem', backgroundColor: 'white', padding: '1rem', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                      <h4 style={{ margin: '0 0 0.5rem 0', color: '#4b5563' }}>🤖 AI Diagnosis</h4>
                      <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{failure.diagnosis.explanation}</p>
                      
                      {failure.diagnosis.suggested_fix && (
                        <div>
                          <p style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#6b7280' }}>Suggested Fix:</p>
                          <pre style={{ 
                            backgroundColor: '#f3f4f6', 
                            padding: '0.5rem', 
                            borderRadius: '0.25rem', 
                            overflowX: 'auto',
                            fontSize: '0.8rem'
                          }}>
                            {failure.diagnosis.suggested_fix}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}