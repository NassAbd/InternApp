import React from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import styles from './NotificationContainer.module.css';

const NotificationContainer: React.FC = () => {
    const { notifications, removeNotification } = useNotifications();

    if (notifications.length === 0) {
        return null;
    }

    return (
        <div className={styles.container}>
            {notifications.map((notification) => (
                <div
                    key={notification.id}
                    className={`${styles.notification} ${styles[notification.type]}`}
                >
                    <div className={styles.content}>
                        <div className={styles.icon}>
                            {notification.type === 'success' && '✅'}
                            {notification.type === 'error' && '❌'}
                            {notification.type === 'info' && 'ℹ️'}
                            {notification.type === 'warning' && '⚠️'}
                        </div>
                        <div className={styles.text}>
                            <div className={styles.title}>{notification.title}</div>
                            {notification.message && (
                                <div className={styles.message}>{notification.message}</div>
                            )}
                        </div>
                        <button
                            onClick={() => removeNotification(notification.id)}
                            className={styles.closeButton}
                            aria-label="Close notification"
                        >
                            ×
                        </button>
                    </div>
                    <div className={styles.progressBar}>
                        <div
                            className={styles.progressFill}
                            style={{
                                animationDuration: `${notification.duration}ms`,
                                animationName: styles.progress
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
};

export default NotificationContainer;