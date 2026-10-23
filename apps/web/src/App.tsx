import { Routes, Route } from "react-router-dom";
import LandingPage from "./routes/LandingPage";
import CustomerPage from "./routes/CustomerPage";
import AgentPage from "./routes/AgentPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/customer" element={<CustomerPage />} />
      <Route path="/agent" element={<AgentPage />} />
    </Routes>
  );
}
