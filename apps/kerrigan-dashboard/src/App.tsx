const APP_VERSION = `v${__APP_VERSION__}`;

function App() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-neutral-bg text-neutral-fg font-sans">
      <header className="flex h-13 shrink-0 items-center border-b border-[#1E2530] bg-neutral-bg px-5">
        <h1 className="text-heading font-semibold tracking-[-0.02em] text-brand">
          kerrigan
        </h1>
        <span className="ml-2 rounded border border-[#2A3342] px-2 py-1 text-nano text-[#8B94A6]">
          {APP_VERSION}
        </span>
      </header>

      <main className="flex-1 overflow-hidden p-5">
        <section className="h-full rounded-lg border border-[#1E2530] bg-[#101724] p-6">
          <p className="text-body text-[#A2AAB8]">Dashboard shell placeholder</p>
        </section>
      </main>
    </div>
  );
}

export default App;
