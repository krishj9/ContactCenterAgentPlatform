import { Routes, Route } from "react-router-dom";
import LandingPage from "./routes/LandingPage";
import CustomerView from "./routes/CustomerView";
import AgentCockpit from "./routes/AgentCockpit";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/customer" element={<CustomerView />} />
      <Route path="/agent" element={<AgentCockpit />} />
    </Routes>
  );
}
