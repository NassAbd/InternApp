import styles from "./FeedToggle.module.css";

export type FeedType = "all" | "for-you";

type Props = {
    selectedFeed: FeedType;
    onFeedChange: (feed: FeedType) => void;
    hasPersonalizedResults?: boolean;
};

export function FeedToggle({ selectedFeed, onFeedChange, hasPersonalizedResults = true }: Props) {
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
            </div>

            {selectedFeed === "for-you" && !hasPersonalizedResults && (
                <div className={styles.noResultsMessage}>
                    <p>No personalized results found. Set up your profile to get personalized job recommendations!</p>
                </div>
            )}
        </div>
    );
}