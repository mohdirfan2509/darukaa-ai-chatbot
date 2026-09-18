import { NavLink, Route, Routes } from "react-router-dom";
import { AssistantPage } from "./pages/AssistantPage";
import { ContextPage } from "./pages/ContextPage";
import { DemoPage } from "./pages/DemoPage";
import { HistoryPage } from "./pages/HistoryPage";
import { RetrievalPage } from "./pages/RetrievalPage";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1 className="brand">
          Darukaa.Earth
          <span>AI Biodiversity Intelligence</span>
        </h1>
        <nav className="nav">
          <NavLink to="/" end>
            AI Assistant
          </NavLink>
          <NavLink to="/history">History</NavLink>
          <NavLink to="/context">Environmental Context</NavLink>
          <NavLink to="/retrieval">Knowledge Retrieval</NavLink>
          <NavLink to="/demo">Demo Mode</NavLink>
        </nav>
        <p className="muted" style={{ fontSize: "0.75rem", marginTop: "auto" }}>
          RAG · multi-metric reasoning · evidence validation
        </p>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<AssistantPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/context" element={<ContextPage />} />
          <Route path="/retrieval" element={<RetrievalPage />} />
          <Route path="/demo" element={<DemoPage />} />
        </Routes>
      </main>
    </div>
  );
}
