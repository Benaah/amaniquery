import { useState, useEffect, useCallback } from 'react';
import { AppState, AppStateStatus } from 'react-native';

interface NetworkState {
    isConnected: boolean;
    isInternetReachable: boolean | null;
    type: string | null;
}

export function useNetwork() {
    const [networkState, setNetworkState] = useState<NetworkState>({
        isConnected: true,
        isInternetReachable: true,
        type: 'unknown',
    });
    const [isChecking, setIsChecking] = useState(false);

    const checkConnectivity = useCallback(async () => {
        setIsChecking(true);
        try {
            // Simple connectivity check by trying to fetch a small resource
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const response = await fetch('https://www.google.com/generate_204', {
                method: 'HEAD',
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            setNetworkState({
                isConnected: true,
                isInternetReachable: response.ok || response.status === 204,
                type: 'unknown',
            });
        } catch (error) {
            setNetworkState({
                isConnected: false,
                isInternetReachable: false,
                type: 'none',
            });
        } finally {
            setIsChecking(false);
        }
    }, []);

    useEffect(() => {
        // Check on mount
        checkConnectivity();

        // Check when app comes to foreground
        const subscription = AppState.addEventListener(
            'change',
            (nextAppState: AppStateStatus) => {
                if (nextAppState === 'active') {
                    checkConnectivity();
                }
            },
        );

        // Periodic check every 30 seconds
        const interval = setInterval(checkConnectivity, 30000);

        return () => {
            subscription?.remove();
            clearInterval(interval);
        };
    }, [checkConnectivity]);

    return {
        ...networkState,
        isChecking,
        refresh: checkConnectivity,
    };
}
