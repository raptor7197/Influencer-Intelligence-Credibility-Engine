import { useEffect, useRef } from 'react';

type EventHandler = (event: { type: string; data: Record<string, unknown> }) => void;

export function useSse(onEvent: EventHandler) {
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    const es = new EventSource('/api/events');
    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        handlerRef.current(event);
      } catch {
        // ignore malformed events
      }
    };
    es.onerror = () => {
      // SSE will auto-reconnect
    };
    return () => es.close();
  }, []);
}
