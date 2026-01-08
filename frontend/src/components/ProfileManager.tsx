import { useState, useEffect } from "react";
import { useNotifications } from "../contexts/NotificationContext";
import styles from "./ProfileManager.module.css";

interface UserProfile {
    tags: string[];
    location?: string;
    groq_api_key?: string;
    use_for_scraper_fix?: boolean;
}

interface ProfileManagerProps {
    onClose?: () => void;
    onProfileUpdate?: () => void; // Callback to refresh "For You" feed
}

const PREDEFINED_CATEGORIES = [
    "aerospace",
    "software",
    "engineering",
    "electronics",
    "data",
    "management",
    "operations_supply",
    "research",
    "design",
    "security",
    "finance",
    "marketing"
];

export function ProfileManager({ onClose, onProfileUpdate }: ProfileManagerProps) {
    const [profile, setProfile] = useState<UserProfile>({ tags: [] });
    const [originalProfile, setOriginalProfile] = useState<UserProfile>({ tags: [] });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [resetting, setResetting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { addNotification } = useNotifications();

    // Load profile on component mount
    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch("http://localhost:8000/profile");

            if (!response.ok) {
                throw new Error(`Failed to load profile: ${response.statusText}`);
            }

            const profileData = await response.json();
            setProfile(profileData);
            setOriginalProfile(profileData);
        } catch (err) {
            console.error("Error loading profile:", err);
            setError(err instanceof Error ? err.message : "Failed to load profile");
            // Set default empty profile on error
            const defaultProfile = { tags: [] };
            setProfile(defaultProfile);
            setOriginalProfile(defaultProfile);
        } finally {
            setLoading(false);
        }
    };

    const saveProfile = async () => {
        try {
            setSaving(true);
            setError(null);

            const response = await fetch("http://localhost:8000/profile", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(profile),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to save profile: ${response.statusText}`);
            }

            const savedProfile = await response.json();
            setProfile(savedProfile);
            setOriginalProfile(savedProfile);

            // Show global notification
            addNotification({
                type: 'success',
                title: 'Profile Updated Successfully',
                message: 'Your preferences have been saved and will be used for personalized job recommendations.',
                duration: 4000
            });

            // Notify parent to refresh "For You" feed
            onProfileUpdate?.();

        } catch (err) {
            console.error("Error saving profile:", err);
            setError(err instanceof Error ? err.message : "Failed to save profile");
        } finally {
            setSaving(false);
        }
    };

    const resetProfile = async () => {
        try {
            setResetting(true);
            setError(null);

            const response = await fetch("http://localhost:8000/profile", {
                method: "DELETE",
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to reset profile: ${response.statusText}`);
            }

            const resetProfileData = await response.json();
            setProfile(resetProfileData);
            setOriginalProfile(resetProfileData);

            // Show global notification
            addNotification({
                type: 'info',
                title: 'Profile Reset to Default',
                message: 'All preferences have been cleared. You can now set up your profile from scratch.',
                duration: 4000
            });

            // Notify parent to refresh "For You" feed
            onProfileUpdate?.();

        } catch (err) {
            console.error("Error resetting profile:", err);
            setError(err instanceof Error ? err.message : "Failed to reset profile");
        } finally {
            setResetting(false);
        }
    };

    const handleTagToggle = (tag: string) => {
        setProfile(prev => ({
            ...prev,
            tags: prev.tags.includes(tag)
                ? prev.tags.filter(t => t !== tag)
                : [...prev.tags, tag]
        }));
    };

    const handleLocationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setProfile(prev => ({
            ...prev,
            location: e.target.value
        }));
    };

    const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setProfile(prev => ({
            ...prev,
            groq_api_key: e.target.value
        }));
    };

    const clearError = () => setError(null);

    // Check if current profile differs from saved profile
    const hasUnsavedChanges = () => {
        return JSON.stringify(profile) !== JSON.stringify(originalProfile);
    };

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <h2 className={styles.title}>Profile Manager</h2>
                    {onClose && (
                        <button onClick={onClose} className={styles.closeButton}>
                            ×
                        </button>
                    )}
                </div>
                <div className={styles.loading}>
                    <div className={styles.loader}></div>
                    <p>Loading profile...</p>
                </div>
            </div>
        );
    }


    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>Profile Manager</h2>
                {onClose && (
                    <button onClick={onClose} className={styles.closeButton}>
                        ×
                    </button>
                )}
            </div>

            {/* Error Messages */}
            {error && (
                <div className={styles.errorMessage}>
                    <span>{error}</span>
                    <button onClick={clearError} className={styles.messageClose}>×</button>
                </div>
            )}

            {/* Default Empty State */}
            <div className={styles.emptyState}>
                <p>
                    Set up your profile to receive personalized job recommendations.
                    Select your areas of interest and preferred location to get started.
                </p>
            </div>

            <div className={styles.content}>
                {/* Interest Tags Section */}
                <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>Areas of Interest</h3>
                    <p className={styles.sectionDescription}>
                        Select the categories that match your interests and career goals:
                    </p>

                    <div className={styles.tagsContainer}>
                        {PREDEFINED_CATEGORIES.map(category => (
                            <label key={category} className={styles.tagLabel}>
                                <input
                                    type="checkbox"
                                    checked={profile.tags.includes(category)}
                                    onChange={() => handleTagToggle(category)}
                                    className={styles.tagCheckbox}
                                />
                                <span className={styles.tagText}>
                                    {category.charAt(0).toUpperCase() + category.slice(1)}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Location Preference Section */}
                <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>Location Preference</h3>
                    <p className={styles.sectionDescription}>
                        Enter your preferred job location (optional):
                    </p>

                    <input
                        type="text"
                        value={profile.location || ""}
                        onChange={handleLocationChange}
                        placeholder="e.g., Paris, London"
                        className={styles.locationInput}
                    />
                </div>

                {/* API Key Section */}
                <div className={styles.section}>
                    <h3 className={styles.sectionTitle}>Groq API Key (Optional)</h3>
                    <p className={styles.sectionDescription}>
                        Provide your Groq API key to enable CV parsing and AI-powered scraper diagnosis:
                    </p>

                    <input
                        type="password"
                        value={profile.groq_api_key || ""}
                        onChange={handleApiKeyChange}
                        placeholder="Enter your Groq API key"
                        className={styles.apiKeyInput}
                    />

                    <p className={styles.apiKeyNote}>
                        Your API key is stored locally and used for CV analysis and diagnosing broken scrapers.
                    </p>

                    <div style={{ marginTop: '15px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={profile.use_for_scraper_fix || false}
                                onChange={(e) => setProfile(prev => ({
                                    ...prev,
                                    use_for_scraper_fix: e.target.checked
                                }))}
                                style={{ marginRight: '10px', width: '16px', height: '16px' }}
                            />
                            <span style={{ fontWeight: 500, color: '#374151' }}>
                                Enable AI diagnosis for broken scrapers
                            </span>
                        </label>
                        <p className={styles.apiKeyNote} style={{ marginTop: '5px', marginLeft: '26px' }}>
                            If enabled, the system will use your API key to automatically analyze scraper errors and suggest fixes.
                        </p>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className={styles.actions}>
                    <button
                        onClick={saveProfile}
                        disabled={saving || resetting}
                        className={`${styles.saveButton} ${hasUnsavedChanges() ? styles.hasChanges : ''}`}
                    >
                        {saving ? "Saving..." : "Save Profile"}
                        {hasUnsavedChanges() && !saving && <span className={styles.changeIndicator}>*</span>}
                    </button>

                    <button
                        onClick={resetProfile}
                        disabled={loading || saving || resetting}
                        className={styles.resetButton}
                    >
                        {resetting ? "Resetting..." : "Reset to Default"}
                    </button>
                </div>
            </div>
        </div>
    );
}