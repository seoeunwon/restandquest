import { Routes, Route, useNavigate } from "react-router-dom";
import FirstPage from "./firstpage";
import AppContent from "./appcontent";

function App() {
  const navigate = useNavigate();

  return (
    <Routes>
      <Route
        path="/"
        element={<FirstPage onStart={() => navigate("/main")} />}
      />
      <Route path="/main" element={<AppContent />} />
    </Routes>
  );
}

export default App;
