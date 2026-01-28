import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./layouts/dashboard";
import PrivateRoute from "./auth/PrivateRoute";
import { SignIn } from "./pages/auth/sign-in";  
import { SignUp } from "./pages/auth/sign-up";  
import { AuthProvider } from "@/context/AuthContext";

function App() {
  return (
    <AuthProvider>
      <Routes>
    
        <Route path="/dashboard/*" element={
          <PrivateRoute>
             <Dashboard />
          </PrivateRoute>
        } />
        

        <Route path="/auth/sign-in" element={<SignIn />} />
        <Route path="/auth/sign-up" element={<SignUp />} />
        
      
        <Route path="*" element={<Navigate to="/auth/sign-up" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;