import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import {
  RefreshCw,
  LogOut,
  Play,
  Pause,
  Moon,
  Sun,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Activity,
} from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";
import OptionChainModal from "@/components/OptionChainModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

const AUTO_REFRESH_INTERVAL = 30 * 60 * 1000; // 30 minutes in milliseconds

const DashboardPage = ({ token, username, onLogout }) => {
  const [dashboardData, setDashboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const { theme, setTheme } = useTheme();

  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/market/dashboard`, {
        params: { token },
      });

      if (response.data.success) {
        setDashboardData(response.data.data);
        setLastUpdated(new Date(response.data.timestamp));
      } else {
        toast.error("Failed to fetch dashboard data");
      }
    } catch (error) {
      console.error("Dashboard data error:", error);
      toast.error("Error fetching market data");
    }
  }, [token]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
    toast.success("Data refreshed successfully");
  };

  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled(!autoRefreshEnabled);
    toast.info(
      autoRefreshEnabled
        ? "Auto-refresh paused"
        : "Auto-refresh resumed (30 min interval)"
    );
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  const handleViewChain = (stock) => {
    setSelectedStock(stock);
  };

  // Initial data fetch
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await fetchDashboardData();
      setLoading(false);
    };
    loadInitialData();
  }, [fetchDashboardData]);

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefreshEnabled) return;

    const interval = setInterval(() => {
      fetchDashboardData();
      toast.info("Auto-refresh: Data updated");
    }, AUTO_REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchDashboardData]);

  const formatNumber = (num) => {
    if (num === null || num === undefined) return "--";
    if (num >= 10000000) return `${(num / 10000000).toFixed(2)}Cr`;
    if (num >= 100000) return `${(num / 100000).toFixed(2)}L`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const formatPrice = (price) => {
    if (price === null || price === undefined) return "--";
    return parseFloat(price).toFixed(2);
  };

  const getSignalBadge = (signal) => {
    if (!signal) return null;

    const badges = {
      Bullish: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
      Bearish: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
      Neutral: "bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20",
      "High Volatility": "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
    };

    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${badges[signal] || badges.Neutral}`}
      >
        {signal === "High Volatility" && <Activity className="w-3 h-3 mr-1" />}
        {signal}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400">Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950" data-testid="dashboard-page">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                    TrueData Analytics
                  </h1>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Welcome, {username}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Last Updated */}
              {lastUpdated && (
                <div className="hidden md:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mr-2">
                  <span>Last updated:</span>
                  <span className="font-medium">
                    {lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
              )}

              {/* Auto-refresh toggle */}
              <Button
                data-testid="auto-refresh-toggle"
                variant="outline"
                size="sm"
                onClick={toggleAutoRefresh}
                className="gap-2"
              >
                {autoRefreshEnabled ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">
                  {autoRefreshEnabled ? "Pause" : "Resume"}
                </span>
              </Button>

              {/* Manual refresh */}
              <Button
                data-testid="manual-refresh-button"
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="gap-2"
              >
                <RefreshCw
                  className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
                />
                <span className="hidden sm:inline">Refresh</span>
              </Button>

              {/* Theme toggle */}
              <Button
                data-testid="theme-toggle"
                variant="outline"
                size="sm"
                onClick={toggleTheme}
              >
                {theme === "dark" ? (
                  <Sun className="w-4 h-4" />
                ) : (
                  <Moon className="w-4 h-4" />
                )}
              </Button>

              {/* Logout */}
              <Button
                data-testid="logout-button"
                variant="destructive"
                size="sm"
                onClick={onLogout}
                className="gap-2"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4 max-w-[1600px] mx-auto">
        <Card className="shadow-lg">
          <CardHeader className="border-b border-slate-200 dark:border-slate-800">
            <CardTitle className="text-lg font-semibold">
              Top 20 F&O Stocks - Live Market Data
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="stocks-table">
                <thead className="bg-slate-100 dark:bg-slate-800/50">
                  <tr>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Spot
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Change %
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Volume
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      IV
                    </th>
                    <th className="text-right px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      IV %ile
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Signal
                    </th>
                    <th className="text-center px-4 py-3 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                      Chain
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {dashboardData.map((stock, index) => (
                    <tr
                      key={stock.symbol}
                      data-testid={`stock-row-${stock.symbol}`}
                      className="table-row-hover"
                    >
                      <td className="px-4 py-4">
                        <span className="font-semibold text-slate-900 dark:text-white">
                          {stock.symbol}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right mono font-medium text-slate-900 dark:text-white">
                        {formatPrice(stock.spot)}
                      </td>
                      <td className="px-4 py-4 text-right mono font-semibold">
                        {stock.change_percent !== null && stock.change_percent !== undefined ? (
                          <span
                            className={`inline-flex items-center gap-1 ${
                              stock.change_percent >= 0 ? "positive" : "negative"
                            }`}
                          >
                            {stock.change_percent >= 0 ? (
                              <TrendingUp className="w-4 h-4" />
                            ) : (
                              <TrendingDown className="w-4 h-4" />
                            )}
                            {stock.change_percent >= 0 ? "+" : ""}
                            {stock.change_percent.toFixed(2)}%
                          </span>
                        ) : (
                          "--"
                        )}
                      </td>
                      <td className="px-4 py-4 text-right mono text-sm text-slate-600 dark:text-slate-400">
                        {formatNumber(stock.volume)}
                      </td>
                      <td className="px-4 py-4 text-right mono text-sm text-slate-600 dark:text-slate-400">
                        {stock.iv ? `${stock.iv}%` : "--"}
                      </td>
                      <td className="px-4 py-4 text-right mono text-sm text-slate-600 dark:text-slate-400">
                        {stock.iv_percentile ? `${stock.iv_percentile}%` : "--"}
                      </td>
                      <td className="px-4 py-4">
                        {stock.error ? (
                          <span className="text-xs text-red-500 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />
                            Error
                          </span>
                        ) : (
                          getSignalBadge(stock.signal)
                        )}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <Button
                          data-testid={`view-chain-${stock.symbol}`}
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewChain(stock)}
                          className="text-xs"
                        >
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Auto-refresh status */}
        {autoRefreshEnabled && (
          <div className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
            <Activity className="w-4 h-4 inline mr-1" />
            Auto-refresh enabled - Updates every 30 minutes
          </div>
        )}
      </main>

      {/* Option Chain Modal */}
      {selectedStock && (
        <OptionChainModal
          stock={selectedStock}
          token={token}
          onClose={() => setSelectedStock(null)}
        />
      )}
    </div>
  );
};

export default DashboardPage;
