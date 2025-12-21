/**
 * Toast notification utilities for the Laundromat Tycoon UI.
 * 
 * Uses react-hot-toast with custom styling to match the cyberpunk theme.
 * 
 * Usage:
 *   import { showSuccess, showError, showInfo } from './toast';
 *   showSuccess('Price updated!');
 *   showError('Insufficient funds');
 */

import toast, { Toaster } from 'react-hot-toast';

// ! Custom toast styling matching the Executive War Room theme
const toastStyles = {
    style: {
        background: 'rgba(3, 5, 8, 0.95)',
        color: '#e2e8f0',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(12px)',
        fontFamily: 'Inter, sans-serif',
        fontSize: '14px',
        padding: '12px 16px',
        borderRadius: '8px',
    },
};

/**
 * Show a success toast with neon green accent.
 */
export const showSuccess = (message: string) => {
    toast.success(message, {
        ...toastStyles,
        iconTheme: {
            primary: '#39ff14', // neon-green
            secondary: '#030508',
        },
    });
};

/**
 * Show an error toast with neon pink/red accent.
 */
export const showError = (message: string) => {
    toast.error(message, {
        ...toastStyles,
        iconTheme: {
            primary: '#ff006e', // neon-pink
            secondary: '#030508',
        },
        duration: 5000, // Errors stay longer
    });
};

/**
 * Show an info toast with neon cyan accent.
 */
export const showInfo = (message: string) => {
    toast(message, {
        ...toastStyles,
        icon: '📢',
    });
};

/**
 * Show a loading toast (returns an ID to dismiss later).
 */
export const showLoading = (message: string): string => {
    return toast.loading(message, {
        ...toastStyles,
    });
};

/**
 * Dismiss a specific toast by ID.
 */
export const dismissToast = (toastId: string) => {
    toast.dismiss(toastId);
};

/**
 * Toast container component.
 * Add this to your App.tsx at the root level.
 */
export const ToastContainer = () => (
    <Toaster
        position="bottom-right"
        gutter={8}
        containerStyle={{
            bottom: 80, // Above the bottom HUD elements
        }}
        toastOptions={{
            duration: 3000,
        }}
    />
);

export default toast;
