import React from 'react';
import styles from './TrackButton.module.css';
import type { Job } from '../hooks/useApplicationTracker';

interface TrackButtonProps {
    job: Job;
    isTracked: boolean;
    onTrack: (job: Job) => void;
    onUntrack: (jobId: string) => void;
    loading?: boolean;
}

export function TrackButton({ job, isTracked, onTrack, onUntrack, loading = false }: TrackButtonProps) {
    // Generate job ID using the same logic as the hook
    const generateJobId = (job: Job): string => {
        return btoa(job.link).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
    };

    const handleClick = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();

        if (loading) return;

        if (isTracked) {
            const jobId = generateJobId(job);
            onUntrack(jobId);
        } else {
            onTrack(job);
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={loading}
            className={`${styles.trackButton} ${isTracked ? styles.tracked : styles.untracked
                } ${loading ? styles.loading : ''}`}
            title={isTracked ? 'Remove from tracking' : 'Track this job'}
        >
            {loading ? (
                <span className={styles.spinner} />
            ) : isTracked ? (
                <>
                    <span className={styles.icon}>✓</span>
                    <span className={styles.text}>Tracked</span>
                </>
            ) : (
                <>
                    <span className={styles.icon}>+</span>
                    <span className={styles.text}>Track</span>
                </>
            )}
        </button>
    );
}