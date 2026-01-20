// frontend/hooks/useWebSocket.ts
import { useEffect, useState, useCallback, useRef } from 'react';

interface WebSocketHook {
    lastMessage: MessageEvent | null;
    sendMessage: (message: string) => void;
    connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

export function useWebSocket(url: string): WebSocketHook {
    const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const wsUrl = url.startsWith('/')
            ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`
            : url;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setConnectionStatus('connected');
        };

        ws.onmessage = (event) => {
            setLastMessage(event);
        };

        ws.onclose = () => {
            setConnectionStatus('disconnected');
        };

        ws.onerror = () => {
            setConnectionStatus('disconnected');
        };

        return () => {
            ws.close();
        };
    }, [url]);

    const sendMessage = useCallback((message: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(message);
        }
    }, []);

    return { lastMessage, sendMessage, connectionStatus };
}
