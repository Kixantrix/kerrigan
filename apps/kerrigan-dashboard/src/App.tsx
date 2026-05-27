import { BrowserRouter, Route, Routes } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PortfolioPlaceholderRoute />} />
      </Routes>
    </BrowserRouter>
  );
}

function PortfolioPlaceholderRoute() {
  return (
    <main className="h-full overflow-hidden bg-bg text-fg">
      <div className="mx-auto flex h-full w-full max-w-[1280px] flex-col gap-4 px-6 py-5">
        <header className="rounded-2xl border border-brand/35 bg-surface/80 px-6 py-4">
          <p className="text-micro uppercase tracking-[0.2em] text-accent">
            kerrigan-dashboard
          </p>
          <h1 className="text-display font-semibold">
            Portfolio route placeholder
          </h1>
          <p className="text-body text-fg/80">
            Scaffold ready (Tauri 2 + Vite + React + TypeScript + Tailwind 4).
          </p>
        </header>
        <section className="grid flex-1 grid-cols-3 gap-4 overflow-hidden">
          <article className="rounded-2xl border border-fg/10 bg-surface/80 p-4" />
          <article className="rounded-2xl border border-fg/10 bg-surface/80 p-4" />
          <article className="rounded-2xl border border-fg/10 bg-surface/80 p-4" />
        </section>
      </div>
    </main>
  );
}

export default App;
