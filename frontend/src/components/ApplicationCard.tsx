import { useState } from 'react';
import { type Application, type ApplicationStatus } from '../hooks/useApplicationTracker';
import styles from './ApplicationCard.module.css';

// Status columns configuration for dropdown options with enhanced visual indicators
const STATUS_OPTIONS: {
    status: ApplicationStatus;
    label: string;
    color: string;
    icon: string;
}[] = [
        { status: 'Interested', label: 'Interested', color: '#6b7280', icon: '👀' },
        { status: 'Applied', label: 'Applied', color: '#3b82f6', icon: '📝' },
        { status: 'Interview', label: 'Interview', color: '#8b5cf6', icon: '🎯' },
        { status: 'Offer', label: 'Offer', color: '#10b981', icon: '🎉' },
        { status: 'Rejected', label: 'Rejected', color: '#ef4444', icon: '❌' }
    ];

interface ApplicationCardProps {
    application: Application;
    onStatusUpdate: (jobId: string, status: ApplicationStatus) => void;
    onNotesUpdate: (jobId: string, notes: string) => void;
    onRemove: (jobId: string) => void;
}

export function ApplicationCard({ application, onStatusUpdate, onNotesUpdate, onRemove }: ApplicationCardProps) {
    const [isEditingNotes, setIsEditingNotes] = useState(false);
    const [notesValue, setNotesValue] = useState(application.notes || '');
    const [isUpdating, setIsUpdating] = useState(false);

    const currentStatusOption = STATUS_OPTIONS.find(option => option.status === application.status);

    const handleStatusChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newStatus = e.target.value as ApplicationStatus;
        // Status validation - only allow valid enum values
        const validStatuses: ApplicationStatus[] = ['Interested', 'Applied', 'Interview', 'Offer', 'Rejected'];
        if (validStatuses.includes(newStatus)) {
            setIsUpdating(true);
            try {
                await onStatusUpdate(application.id, newStatus);
            } finally {
                setIsUpdating(false);
            }
        }
    };

    const handleNotesSubmit = async () => {
        setIsUpdating(true);
        try {
            await onNotesUpdate(application.id, notesValue);
            setIsEditingNotes(false);
        } finally {
            setIsUpdating(false);
        }
    };

    const handleNotesCancel = () => {
        setNotesValue(application.notes || '');
        setIsEditingNotes(false);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <div
            className={`${styles.applicationCard} ${isUpdating ? styles.updating : ''}`}
            data-testid="application-card"
            data-status={application.status}
        >
            {isUpdating && <div className={styles.updateOverlay} />}

            <div className={styles.cardHeader}>
                <h3 className={styles.jobTitle}>{application.job.title}</h3>
                <button
                    onClick={() => onRemove(application.id)}
                    className={styles.removeButton}
                    title="Remove from tracking"
                    aria-label="Remove application from tracking"
                    disabled={isUpdating}
                >
                    ×
                </button>
            </div>

            <div className={styles.cardContent}>
                <div className={styles.companyInfo}>
                    <span className={styles.company}>{application.job.company}</span>
                    <span className={styles.location}>{application.job.location}</span>
                </div>

                <div className={styles.statusSection}>
                    <label htmlFor={`status-${application.id}`} className={styles.statusLabel}>
                        Status:
                    </label>
                    <div className={styles.statusSelectWrapper}>
                        <span
                            className={styles.statusIndicator}
                            style={{ backgroundColor: currentStatusOption?.color }}
                        >
                            {currentStatusOption?.icon}
                        </span>
                        <select
                            id={`status-${application.id}`}
                            data-testid="status-select"
                            value={application.status}
                            onChange={handleStatusChange}
                            className={styles.statusSelect}
                            aria-label="Application status"
                            disabled={isUpdating}
                        >
                            {STATUS_OPTIONS.map(option => (
                                <option key={option.status} value={option.status}>
                                    {option.icon} {option.label}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className={styles.notesSection}>
                    <div className={styles.notesHeader}>
                        <span className={styles.notesLabel}>Notes:</span>
                        {!isEditingNotes && (
                            <button
                                onClick={() => setIsEditingNotes(true)}
                                className={styles.editNotesButton}
                                aria-label={application.notes ? 'Edit notes' : 'Add notes'}
                            >
                                {application.notes ? 'Edit' : 'Add'}
                            </button>
                        )}
                    </div>

                    {isEditingNotes ? (
                        <div className={styles.notesEditor}>
                            <textarea
                                value={notesValue}
                                onChange={(e) => setNotesValue(e.target.value)}
                                placeholder="Add your notes about this application..."
                                className={styles.notesTextarea}
                                rows={3}
                                aria-label="Application notes"
                            />
                            <div className={styles.notesActions}>
                                <button
                                    onClick={handleNotesSubmit}
                                    className={styles.saveButton}
                                    aria-label="Save notes"
                                    disabled={isUpdating}
                                >
                                    {isUpdating ? '...' : 'Save'}
                                </button>
                                <button
                                    onClick={handleNotesCancel}
                                    className={styles.cancelButton}
                                    aria-label="Cancel editing notes"
                                    disabled={isUpdating}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.notesDisplay}>
                            {application.notes ? (
                                <p className={styles.notesText}>{application.notes}</p>
                            ) : (
                                <p className={styles.noNotes}>No notes added yet</p>
                            )}
                        </div>
                    )}
                </div>

                <div className={styles.cardFooter}>
                    <div className={styles.dates}>
                        <span className={styles.dateLabel}>Added:</span>
                        <span className={styles.dateValue}>{formatDate(application.date_added)}</span>
                    </div>
                    <div className={styles.dates}>
                        <span className={styles.dateLabel}>Updated:</span>
                        <span className={styles.dateValue}>{formatDate(application.last_update)}</span>
                    </div>
                    <a
                        href={application.job.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.jobLink}
                        aria-label={`View job posting for ${application.job.title} at ${application.job.company}`}
                    >
                        View Job
                    </a>
                </div>
            </div>
        </div>
    );
}