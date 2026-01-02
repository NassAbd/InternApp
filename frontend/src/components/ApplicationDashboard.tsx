import { useMemo } from 'react';
import { useApplicationTracker, type Application, type ApplicationStatus } from '../hooks/useApplicationTracker';
import { ApplicationCard } from './ApplicationCard';
import styles from './ApplicationDashboard.module.css';

// Status columns configuration for Kanban-style layout with enhanced visual indicators
const STATUS_COLUMNS: {
    status: ApplicationStatus;
    label: string;
    color: string;
    icon: string;
    bgColor: string;
}[] = [
        { status: 'Interested', label: 'Interested', color: '#6b7280', icon: '👀', bgColor: '#f9fafb' },
        { status: 'Applied', label: 'Applied', color: '#3b82f6', icon: '📝', bgColor: '#eff6ff' },
        { status: 'Interview', label: 'Interview', color: '#8b5cf6', icon: '🎯', bgColor: '#faf5ff' },
        { status: 'Offer', label: 'Offer', color: '#10b981', icon: '🎉', bgColor: '#ecfdf5' },
        { status: 'Rejected', label: 'Rejected', color: '#ef4444', icon: '❌', bgColor: '#fef2f2' }
    ];

export function ApplicationDashboard() {
    const { state, updateStatus, updateNotes, untrackJob } = useApplicationTracker();

    // Group applications by status and sort by last_update within each group
    const applicationsByStatus = useMemo(() => {
        const grouped = STATUS_COLUMNS.reduce((acc, column) => {
            acc[column.status] = [];
            return acc;
        }, {} as Record<ApplicationStatus, Application[]>);

        // Group applications by status
        state.applications.forEach(app => {
            if (grouped[app.status]) {
                grouped[app.status].push(app);
            }
        });

        // Sort each group by last_update (most recent first)
        Object.keys(grouped).forEach(status => {
            grouped[status as ApplicationStatus].sort((a, b) =>
                new Date(b.last_update).getTime() - new Date(a.last_update).getTime()
            );
        });

        return grouped;
    }, [state.applications]);

    const totalApplications = state.applications.length;

    if (state.loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loader}>
                    <div className={styles.spinner}></div>
                    <p>Loading applications...</p>
                </div>
            </div>
        );
    }

    if (state.error) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>
                    <h2>Error Loading Applications</h2>
                    <p>{state.error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>Application Dashboard</h1>
                <p className={styles.subtitle}>
                    Track and manage your job applications through every stage of the process
                </p>
                {totalApplications > 0 && (
                    <div className={styles.stats}>
                        <span className={styles.totalCount}>
                            {totalApplications} application{totalApplications !== 1 ? 's' : ''} tracked
                        </span>
                        {STATUS_COLUMNS.map(column => {
                            const count = applicationsByStatus[column.status].length;
                            if (count > 0) {
                                return (
                                    <div key={column.status} className={styles.progressIndicator}>
                                        <div
                                            className={styles.progressDot}
                                            style={{ backgroundColor: column.color }}
                                        />
                                        <span>{column.icon} {count}</span>
                                    </div>
                                );
                            }
                            return null;
                        })}
                    </div>
                )}
            </div>

            {totalApplications === 0 ? (
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>📋</div>
                    <h2 className={styles.emptyTitle}>No applications tracked yet</h2>
                    <p className={styles.emptyMessage}>
                        No applications tracked yet. Start by adding offers from the feed!
                    </p>
                    <a href="/" className={styles.backToFeedButton}>
                        Go to Job Feed
                    </a>
                </div>
            ) : (
                <div className={styles.kanbanBoard}>
                    {STATUS_COLUMNS.map(column => (
                        <div
                            key={column.status}
                            className={styles.statusColumn}
                            data-status={column.status}
                        >
                            <div className={styles.columnHeader}>
                                <h3 className={styles.columnTitle}>
                                    <span className={styles.statusIcon}>{column.icon}</span>
                                    {column.label}
                                </h3>
                                <span className={styles.columnCount}>
                                    {applicationsByStatus[column.status].length}
                                </span>
                            </div>

                            <div className={styles.columnContent}>
                                {applicationsByStatus[column.status].map(application => (
                                    <ApplicationCard
                                        key={application.id}
                                        application={application}
                                        onStatusUpdate={updateStatus}
                                        onNotesUpdate={updateNotes}
                                        onRemove={untrackJob}
                                    />
                                ))}

                                {applicationsByStatus[column.status].length === 0 && (
                                    <div className={styles.emptyColumn}>
                                        <p>No applications in this stage</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}