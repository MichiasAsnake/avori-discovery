type EmptyStateProps = {
  onRunDiscovery?: () => void;
};

export function EmptyState({ onRunDiscovery }: EmptyStateProps) {
  return (
    <section className="flex min-h-[24rem] flex-col items-center justify-center rounded-[1.75rem] border border-dashed border-slate-300 bg-white/70 px-8 text-center shadow-sm">
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-slate-500">
        Avori Discovery
      </p>
      <h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-slate-900">
        Get started
      </h2>
      <p className="mt-4 max-w-xl text-lg leading-8 text-slate-600">
        Click <span className="font-semibold text-slate-900">Run Discovery</span> in the
        sidebar to pull today&apos;s TikTok Shop candidates.
      </p>
      <button
        className="mt-8 rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
        onClick={onRunDiscovery}
        type="button"
      >
        Run Discovery
      </button>
    </section>
  );
}
