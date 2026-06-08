import { PortfolioView } from "./routes/portfolio/PortfolioView.js";
import { HashRouter, Link, Route, Routes } from "react-router-dom";
import { ProjectView } from "./routes/project/ProjectView.js";
import { InboxView } from "./routes/inbox/InboxView.js";

const APP_VERSION = `v${__APP_VERSION__}`;

function App() {
  return (
    <HashRouter>
      <div className="flex h-screen flex-col overflow-hidden bg-neutral-bg font-sans text-neutral-fg">
        <header className="flex h-13 shrink-0 items-center border-b border-[#1E2530] bg-neutral-bg px-5">
          <h1 className="text-heading font-semibold tracking-[-0.02em] text-brand">kerrigan</h1>
          <span className="ml-2 rounded border border-[#2A3342] px-2 py-1 text-nano text-[#8B94A6]">
            {APP_VERSION}
          </span>
          <nav className="ml-6 flex items-center gap-4" aria-label="Main navigation">
            <Link
              to="/"
              className="text-micro text-[#8B94A6] hover:text-neutral-fg"
              data-testid="nav-portfolio"
            >
              Portfolio
            </Link>
            <Link
              to="/inbox"
              className="text-micro text-[#8B94A6] hover:text-neutral-fg"
              data-testid="nav-inbox"
            >
              Inbox
            </Link>
          </nav>
        </header>

        <main className="flex-1 overflow-hidden p-5">
          <Routes>
            <Route path="/" element={<PortfolioView />} />
            <Route path="/project/:projectId" element={<ProjectView />} />
            <Route path="/inbox" element={<InboxView />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}

export default App;
