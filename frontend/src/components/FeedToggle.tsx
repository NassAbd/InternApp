import { useState } from "react";
import styles from "./FeedToggle.module.css";

export type FeedType = "all" | "for-you";

type Props = {
    selectedFeed: FeedType;
    onFeedChange: (feed: FeedType) => void;
    hasPersonalizedResults?: boolean;
};

// Info icon component (simple SVG)
const InfoIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="m9,9 0,0 a3,3 0 1,1 6,0c0,2 -3,3 -3,3"></path>
        <path d="m9,17 h6"></path>
    </svg>
);

// Scoring explanation overlay
const ScoringExplanation = ({ isVisible, onClose }: { isVisible: boolean; onClose: () => void }) => {
    if (!isVisible) return null;

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.explanationCard} onClick={(e) => e.stopPropagation()}>
                <div className={styles.explanationHeader}>
                    <h3>How "For You" Scoring Works</h3>
                    <button onClick={onClose} className={styles.closeButton}>×</button>
                </div>
                <div className={styles.explanationContent}>
                    <p>Jobs are scored based on how well they match your profile:</p>
                    <div className={styles.scoringRules}>
                        <div className={styles.scoringRule}>
                            <span className={styles.points}>+10 points</span>
                            <span className={styles.description}>per matching tag (software, aerospace, etc.)</span>
                        </div>
                        <div className={styles.scoringRule}>
                            <span className={styles.points}>+5 points</span>
                            <span className={styles.description}>for matching your preferred location</span>
                        </div>
                        <div className={styles.scoringRule}>
                            <span className={styles.points}>+2 points</span>
                            <span className={styles.description}>for newly posted jobs</span>
                        </div>
                    </div>
                    <div className={styles.sortInfo}>
                        <strong>Sort Order:</strong> Jobs with the highest scores appear first in your "For You" feed.
                    </div>
                </div>
            </div>
        </div>
    );
};

export function FeedToggle({ selectedFeed, onFeedChange, hasPersonalizedResults = true }: Props) {
    const [showExplanation, setShowExplanation] = useState(false);

    return (
        <div className={styles.container}>
            <div className={styles.toggleGroup}>
                <button
                    className={`${styles.toggleButton} ${selectedFeed === "all" ? styles.active : ""
                        }`}
                    onClick={() => onFeedChange("all")}
                >
                    All Offers
                </button>
                <button
                    className={`${styles.toggleButton} ${selectedFeed === "for-you" ? styles.active : ""
                        }`}
                    onClick={() => onFeedChange("for-you")}
                >
                    For You
                </button>
                <button
                    className={styles.infoButton}
                    onClick={(e) => {
                        e.stopPropagation();
                        setShowExplanation(true);
                    }}
                    title="How scoring works"
                >
                    <InfoIcon />
                </button>
            </div>

            {selectedFeed === "for-you" && !hasPersonalizedResults && (
                <div className={styles.noResultsMessage}>
                    <p>No personalized results found. Set up your profile to get personalized job recommendations!</p>
                </div>
            )}

            <ScoringExplanation
                isVisible={showExplanation}
                onClose={() => setShowExplanation(false)}
            />
        </div>
    );
}