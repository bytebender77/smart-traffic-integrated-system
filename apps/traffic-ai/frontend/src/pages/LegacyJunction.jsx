import { useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

export default function LegacyJunction() {
  const { jid } = useParams();
  const [searchParams] = useSearchParams();

  const legacyApiBaseUrl = useMemo(() => {
    const override = searchParams.get('api');
    return override || import.meta.env.VITE_LEGACY_API_BASE_URL || '';
  }, [searchParams]);

  const [connection, setConnection] = useState({
    state: 'checking',
    detail: null
  });

  useEffect(() => {
    if (!legacyApiBaseUrl) {
      setConnection({
        state: 'missing',
        detail: 'Legacy backend URL is not set. Run ./scripts/start-integrated-random-ports.sh.'
      });
      return;
    }

    let cancelled = false;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    (async () => {
      try {
        const res = await fetch(`${legacyApiBaseUrl}/simulation/status`, {
          signal: controller.signal
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (cancelled) return;
        setConnection({ state: 'ok', detail: null });
      } catch (e) {
        if (cancelled) return;
        setConnection({
          state: 'unreachable',
          detail: `Cannot reach ${legacyApiBaseUrl}. Ensure the legacy backend is running.`
        });
      } finally {
        clearTimeout(timeoutId);
      }
    })();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [legacyApiBaseUrl]);

  const src = useMemo(() => {
    const api = encodeURIComponent(legacyApiBaseUrl || 'http://localhost:8001');
    const safeJid = encodeURIComponent(jid || 'C1');
    return `/legacy/junction.html?jid=${safeJid}&api=${api}`;
  }, [jid, legacyApiBaseUrl]);

  return (
    <div className="w-full">
      {connection.state !== 'ok' && (
        <div className="mb-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
          <div className="font-semibold text-white">Legacy UI status</div>
          <div className="mt-1">{connection.detail || 'Checking backend connectivity...'}</div>
          <div className="mt-2 text-white/50">
            Tip: start both backends with <code>./scripts/start-integrated-random-ports.sh</code>
          </div>
        </div>
      )}
      <iframe
        title="Legacy Junction Dashboard"
        src={src}
        className="h-[calc(100vh-140px)] w-full border-0 md:h-[calc(100vh-110px)]"
      />
    </div>
  );
}

