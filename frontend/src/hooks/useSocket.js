/**
 * Placeholder polling-based "live" hook. The backend doesn't currently
 * expose a websocket, so this polls a given async fetcher on an interval —
 * swap the internals for a real socket.io/websocket client later without
 * changing the call sites (Dashboard.jsx etc just call useLiveData(fetcher)).
 */
import { useEffect, useState, useCallback } from "react";

export function useLiveData(fetcher, intervalMs = 5000, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const result = await fetcher();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
    const id = setInterval(load, intervalMs);
    return () => clearInterval(id);
  }, [load, intervalMs]);

  return { data, error, loading, refetch: load };
}
