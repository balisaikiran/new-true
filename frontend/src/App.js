import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState(null);

  useEffect(() => {
    // Check for existing session
    const savedToken = localStorage.getItem('truedata_token');
    const savedUsername = localStorage.getItem('truedata_username');
    const tokenExpiry = localStorage.getItem('truedata_token_expiry');

    if (savedToken && tokenExpiry) {
      const expiryTime = new Date(tokenExpiry).getTime();
      const currentTime = new Date().getTime();

      if (currentTime < expiryTime) {
        setToken(savedToken);
        setUsername(savedUsername);
        setIsAuthenticated(true);
      } else {
        // Token expired, clear storage
        localStorage.removeItem('truedata_token');
        localStorage.removeItem('truedata_username');
        localStorage.removeItem('truedata_token_expiry');
      }
    }
  }, []);

  const handleLogin = (accessToken, expiresIn, user) => {
    setToken(accessToken);
    setUsername(user);
    setIsAuthenticated(true);

    // Save to localStorage
    localStorage.setItem('truedata_token', accessToken);
    localStorage.setItem('truedata_username', user);
    const expiryTime = new Date(new Date().getTime() + expiresIn * 1000);
    localStorage.setItem('truedata_token_expiry', expiryTime.toISOString());
  };

  const handleLogout = () => {
    setToken(null);
    setUsername(null);
    setIsAuthenticated(false);
    localStorage.removeItem('truedata_token');
    localStorage.removeItem('truedata_username');
    localStorage.removeItem('truedata_token_expiry');
  };

  return (
    <ThemeProvider defaultTheme="dark" storageKey="truedata-theme">
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route
              path="/login"
              element={
                !isAuthenticated ? (
                  <LoginPage onLogin={handleLogin} />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <DashboardPage
                    token={token}
                    username={username}
                    onLogout={handleLogout}
                  />
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </ThemeProvider>
  );
}

export default App;
