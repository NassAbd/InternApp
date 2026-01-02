import { useState, useRef } from "react";
import { useNotifications } from "../contexts/NotificationContext";
import styles from "./CVUploader.module.css";

interface CVUploadResult {
    success: boolean;
    extracted_tags: string[];
    final_tags: string[];
    profile: {
        tags: string[];
        location?: string;
        groq_api_key?: string;
    };
    cv_preview: string;
}

interface CVUploaderProps {
    onUploadSuccess?: (result: CVUploadResult) => void;
    onClose?: () => void;
    onAnalysisStart?: () => void;
    onAnalysisEnd?: () => void;
}

export function CVUploader({ onUploadSuccess, onClose, onAnalysisStart, onAnalysisEnd }: CVUploaderProps) {
    const [file, setFile] = useState<File | null>(null);
    const [apiKey, setApiKey] = useState("");
    const [mergeWithExisting, setMergeWithExisting] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<CVUploadResult | null>(null);
    const [dragOver, setDragOver] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { addNotification } = useNotifications();

    const handleFileSelect = (selectedFile: File) => {
        if (selectedFile.type !== "application/pdf") {
            setError("Only PDF files are supported");
            return;
        }

        if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
            setError("File size must be less than 10MB");
            return;
        }

        setFile(selectedFile);
        setError(null);
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            handleFileSelect(selectedFile);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);

        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) {
            handleFileSelect(droppedFile);
        }
    };

    const handleUpload = async () => {
        if (!file || !apiKey.trim()) {
            setError("Please select a PDF file and provide your Groq API key");
            return;
        }

        try {
            setUploading(true);
            setError(null);
            setResult(null);

            // Notify parent that analysis is starting
            onAnalysisStart?.();

            const formData = new FormData();
            formData.append("file", file);
            formData.append("api_key", apiKey.trim());
            formData.append("merge_with_existing", mergeWithExisting.toString());

            const response = await fetch("http://localhost:8000/profile/parse-cv", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
            }

            const uploadResult: CVUploadResult = await response.json();
            setResult(uploadResult);

            // Show global notification
            addNotification({
                type: 'success',
                title: 'CV Analysis Complete!',
                message: `Successfully extracted ${uploadResult.extracted_tags.length} skills and updated your profile.`,
                duration: 5000
            });

            // Call success callback if provided
            if (onUploadSuccess) {
                onUploadSuccess(uploadResult);
            }

        } catch (err) {
            console.error("Error uploading CV:", err);
            addNotification({
                type: 'error',
                title: 'CV Analysis failed!',
                message: `${err instanceof Error ? err.message : "Failed to upload CV"}`,
                duration: 5000
            });
            //setError(err instanceof Error ? err.message : "Failed to upload CV");
        } finally {
            setUploading(false);
            // Notify parent that analysis is ending
            onAnalysisEnd?.();
        }
    };

    const handleReset = () => {
        setFile(null);
        setApiKey("");
        setError(null);
        setResult(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const clearError = () => setError(null);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>CV Upload & Analysis</h2>
                {onClose && (
                    <button onClick={onClose} className={styles.closeButton}>
                        ×
                    </button>
                )}
            </div>

            {/* Error Message */}
            {error && (
                <div className={styles.errorMessage}>
                    <span>{error}</span>
                    <button onClick={clearError} className={styles.messageClose}>×</button>
                </div>
            )}

            {/* Success Result */}
            {result && (
                <div className={styles.successResult}>
                    <h3 className={styles.resultTitle}>✅ CV Analysis Complete!</h3>

                    <div className={styles.resultSection}>
                        <h4>Extracted Tags:</h4>
                        <div className={styles.tagsList}>
                            {result.extracted_tags.length > 0 ? (
                                result.extracted_tags.map(tag => (
                                    <span key={tag} className={styles.extractedTag}>
                                        {tag}
                                    </span>
                                ))
                            ) : (
                                <span className={styles.noTags}>No specific tags identified</span>
                            )}
                        </div>
                    </div>

                    <div className={styles.resultSection}>
                        <h4>Final Profile Tags:</h4>
                        <div className={styles.tagsList}>
                            {result.final_tags.map(tag => (
                                <span key={tag} className={styles.finalTag}>
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>

                    {result.cv_preview && (
                        <div className={styles.resultSection}>
                            <h4>CV Preview:</h4>
                            <div className={styles.cvPreview}>
                                {result.cv_preview}
                            </div>
                        </div>
                    )}

                    <div className={styles.resultActions}>
                        <button onClick={handleReset} className={styles.resetButton}>
                            Upload Another CV
                        </button>
                    </div>
                </div>
            )}

            {/* Upload Form */}
            {!result && (
                <div className={styles.uploadForm}>
                    {/* API Key Input */}
                    <div className={styles.section}>
                        <h3 className={styles.sectionTitle}>Groq API Key</h3>
                        <p className={styles.sectionDescription}>
                            Enter your Groq API key to enable CV analysis:
                        </p>

                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Enter your Groq API key"
                            className={styles.apiKeyInput}
                            disabled={uploading}
                        />

                        <p className={styles.apiKeyNote}>
                            Your API key is used only for this analysis and stored securely in your profile.
                        </p>
                    </div>

                    {/* File Upload */}
                    <div className={styles.section}>
                        <h3 className={styles.sectionTitle}>Upload CV (PDF)</h3>
                        <p className={styles.sectionDescription}>
                            Select or drag & drop your CV in PDF format:
                        </p>

                        <div
                            className={`${styles.dropZone} ${dragOver ? styles.dragOver : ""} ${file ? styles.hasFile : ""}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf"
                                onChange={handleFileInputChange}
                                className={styles.hiddenFileInput}
                                disabled={uploading}
                            />

                            {file ? (
                                <div className={styles.fileInfo}>
                                    <div className={styles.fileName}>📄 {file.name}</div>
                                    <div className={styles.fileSize}>
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </div>
                                </div>
                            ) : (
                                <div className={styles.dropZoneContent}>
                                    <div className={styles.dropZoneIcon}>📄</div>
                                    <div className={styles.dropZoneText}>
                                        Click to select or drag & drop your CV
                                    </div>
                                    <div className={styles.dropZoneSubtext}>
                                        PDF files only, max 10MB
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Merge Option */}
                    <div className={styles.section}>
                        <label className={styles.checkboxLabel}>
                            <input
                                type="checkbox"
                                checked={mergeWithExisting}
                                onChange={(e) => setMergeWithExisting(e.target.checked)}
                                className={styles.checkbox}
                                disabled={uploading}
                            />
                            <span className={styles.checkboxText}>
                                Merge with existing profile tags
                            </span>
                        </label>
                        <p className={styles.checkboxDescription}>
                            {mergeWithExisting
                                ? "New tags will be added to your existing preferences"
                                : "New tags will replace your current preferences"
                            }
                        </p>
                    </div>

                    {/* Upload Progress */}
                    {uploading && (
                        <div className={styles.uploadProgress}>
                            <div className={styles.progressBar}>
                                <div className={styles.progressFill}></div>
                            </div>
                            <p className={styles.progressText}>
                                Analyzing your CV... This may take a few moments.
                            </p>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className={styles.actions}>
                        <button
                            onClick={handleUpload}
                            disabled={!file || !apiKey.trim() || uploading}
                            className={styles.uploadButton}
                        >
                            {uploading ? "Analyzing CV..." : "Analyze CV"}
                        </button>

                        {file && (
                            <button
                                onClick={handleReset}
                                disabled={uploading}
                                className={styles.clearButton}
                            >
                                Clear
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}