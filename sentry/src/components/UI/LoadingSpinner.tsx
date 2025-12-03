'use client';

export function LoadingSpinner({ label = 'Loading analysis…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-emerald-900/20 bg-white px-4 py-3 text-sm text-emerald-900 shadow-sm">
      <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
