import { useState, useEffect, useCallback } from 'react';
import { useNotifications } from '../contexts/NotificationContext';

// Type definitions based on the backend API and existing Job type
export interface Job {
    id?: number;
    company: string;
    title: string;
    location: string;
    link: string;
    module: string;
    new: boolean;
    tags?: string[];
    match_score?: number;
    matching_tags?: string[];
}

export type ApplicationStatus =
    | 'Interested'
    | 'Applied'
    | 'Interview'
    | 'Offer'
    | 'Rejected';

export interface Application {
    id: string;
    job: Job;
    status: ApplicationStatus;
    date_added: string;
    last_update: string;
    notes?: string;
}

export interface ApplicationState {
    trackedJobs: Set<string>;
    applications: Application[];
    loading: boolean;
    error: string | null;
}

interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

const API_BASE_URL = 'http://localhost:8000';

export function useApplicationTracker() {
    const [state, setState] = useState<ApplicationState>({
        trackedJobs: new Set(),
        applications: [],
        loading: false,
        error: null,
    });

    const { addNotification } = useNotifications();

    // Generate application ID from job data (matches backend logic)
    const generateApplicationId = useCallback((job: Job): string => {
        // Use job link as the unique identifier (matches backend implementation)
        return btoa(job.link).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
    }, []);

    // Load applications from backend
    const loadApplications = useCallback(async () => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/applications`);
            const result: ApiResponse<Application[]> = await response.json();

            if (result.success && result.data) {
                const trackedJobIds = new Set(result.data.map(app => app.id));

                setState(prev => ({
                    ...prev,
                    applications: result.data || [],
                    trackedJobs: trackedJobIds,
                    loading: false,
                }));
            } else {
                throw new Error(result.error || 'Failed to load applications');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            setState(prev => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));

            addNotification({
                type: 'error',
                title: 'Failed to load applications',
                message: errorMessage,
            });
        }
    }, [addNotification]);

    // Track a new job
    const trackJob = useCallback(async (job: Job): Promise<void> => {
        const jobId = generateApplicationId(job);

        // Check if already tracked (idempotence)
        if (state.trackedJobs.has(jobId)) {
            addNotification({
                type: 'info',
                title: 'Job already tracked',
                message: `${job.title} at ${job.company} is already in your tracking list`,
            });
            return;
        }

        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/applications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(job),
            });

            const result: ApiResponse<Application> = await response.json();

            if (result.success && result.data) {
                setState(prev => ({
                    ...prev,
                    applications: [result.data!, ...prev.applications],
                    trackedJobs: new Set([...prev.trackedJobs, result.data!.id]),
                    loading: false,
                }));

                addNotification({
                    type: 'success',
                    title: 'Job tracked successfully',
                    message: `Added ${job.title} at ${job.company} to your tracking list`,
                });
            } else {
                throw new Error(result.error || 'Failed to track job');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            setState(prev => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));

            addNotification({
                type: 'error',
                title: 'Failed to track job',
                message: errorMessage,
            });
        }
    }, [state.trackedJobs, generateApplicationId, addNotification]);

    // Untrack a job
    const untrackJob = useCallback(async (jobId: string): Promise<void> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/applications/${jobId}`, {
                method: 'DELETE',
            });

            const result: ApiResponse<void> = await response.json();

            if (result.success) {
                setState(prev => {
                    const newTrackedJobs = new Set(prev.trackedJobs);
                    newTrackedJobs.delete(jobId);

                    return {
                        ...prev,
                        applications: prev.applications.filter(app => app.id !== jobId),
                        trackedJobs: newTrackedJobs,
                        loading: false,
                    };
                });

                addNotification({
                    type: 'success',
                    title: 'Job untracked',
                    message: 'Removed job from your tracking list',
                });
            } else {
                throw new Error(result.error || 'Failed to untrack job');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            setState(prev => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));

            addNotification({
                type: 'error',
                title: 'Failed to untrack job',
                message: errorMessage,
            });
        }
    }, [addNotification]);

    // Update application status
    const updateStatus = useCallback(async (jobId: string, status: ApplicationStatus): Promise<void> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/applications/${jobId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status }),
            });

            const result: ApiResponse<Application> = await response.json();

            if (result.success && result.data) {
                setState(prev => ({
                    ...prev,
                    applications: prev.applications.map(app =>
                        app.id === jobId ? result.data! : app
                    ),
                    loading: false,
                }));

                addNotification({
                    type: 'success',
                    title: 'Status updated',
                    message: `Application status changed to ${status}`,
                });
            } else {
                throw new Error(result.error || 'Failed to update status');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            setState(prev => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));

            addNotification({
                type: 'error',
                title: 'Failed to update status',
                message: errorMessage,
            });
        }
    }, [addNotification]);

    // Update application notes
    const updateNotes = useCallback(async (jobId: string, notes: string): Promise<void> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/applications/${jobId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notes }),
            });

            const result: ApiResponse<Application> = await response.json();

            if (result.success && result.data) {
                setState(prev => ({
                    ...prev,
                    applications: prev.applications.map(app =>
                        app.id === jobId ? result.data! : app
                    ),
                    loading: false,
                }));

                addNotification({
                    type: 'success',
                    title: 'Notes updated',
                    message: 'Application notes have been saved',
                });
            } else {
                throw new Error(result.error || 'Failed to update notes');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            setState(prev => ({
                ...prev,
                loading: false,
                error: errorMessage,
            }));

            addNotification({
                type: 'error',
                title: 'Failed to update notes',
                message: errorMessage,
            });
        }
    }, [addNotification]);

    // Check if a job is tracked
    const isJobTracked = useCallback((job: Job): boolean => {
        const jobId = generateApplicationId(job);
        return state.trackedJobs.has(jobId);
    }, [state.trackedJobs, generateApplicationId]);

    // Load applications on mount
    useEffect(() => {
        loadApplications();
    }, [loadApplications]);

    return {
        state,
        trackJob,
        untrackJob,
        updateStatus,
        updateNotes,
        isJobTracked,
        loadApplications,
    };
}