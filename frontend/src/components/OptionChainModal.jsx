import { useState, useEffect } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { X, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OptionChainModal = ({ stock, token, onClose }) => {
  const [expiry, setExpiry] = useState("");
  const [optionChainData, setOptionChainData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Set default expiry to next month's last Thursday
  useEffect(() => {
    const getNextExpiry = () => {
      const today = new Date();
      const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
      const lastDay = new Date(nextMonth.getFullYear(), nextMonth.getMonth() + 1, 0);
      
      // Find last Thursday
      let lastThursday = lastDay;
      while (lastThursday.getDay() !== 4) {
        lastThursday.setDate(lastThursday.getDate() - 1);
      }
      
      const day = String(lastThursday.getDate()).padStart(2, '0');
      const month = String(lastThursday.getMonth() + 1).padStart(2, '0');
      const year = lastThursday.getFullYear();
      
      return `${day}-${month}-${year}`;
    };
    
    setExpiry(getNextExpiry());
  }, []);

  const fetchOptionChain = async () => {
    if (!expiry) {
      toast.error("Please enter an expiry date");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/market/optionchain/${stock.symbol}`,
        {
          params: { expiry, token },
        }
      );

      if (response.data.success) {
        setOptionChainData(response.data.data);
        toast.success("Option chain loaded");
      } else {
        toast.error(response.data.error || "Failed to fetch option chain");
      }
    } catch (error) {
      console.error("Option chain error:", error);
      toast.error("Error fetching option chain data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto" data-testid="option-chain-modal">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center justify-between">
            <span>Option Chain - {stock.symbol}</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Expiry selector */}
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <Label htmlFor="expiry" className="mb-2 block">
                Expiry Date (DD-MM-YYYY)
              </Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    id="expiry"
                    data-testid="expiry-input"
                    type="text"
                    placeholder="25-11-2025"
                    value={expiry}
                    onChange={(e) => setExpiry(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button
                  data-testid="load-chain-button"
                  onClick={fetchOptionChain}
                  disabled={loading}
                  className="min-w-[100px]"
                >
                  {loading ? "Loading..." : "Load Chain"}
                </Button>
              </div>
            </div>
          </div>

          {/* Option chain data display */}
          {loading && (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400">Loading option chain...</p>
            </div>
          )}

          {!loading && optionChainData && (
            <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
              <div className="bg-slate-100 dark:bg-slate-800 p-4">
                <h3 className="font-semibold text-lg">Option Chain Data</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {stock.symbol} - Expiry: {expiry}
                </p>
              </div>
              <div className="p-4 max-h-[500px] overflow-auto">
                <pre className="text-xs bg-slate-50 dark:bg-slate-900 p-4 rounded-lg overflow-auto">
                  {JSON.stringify(optionChainData, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {!loading && !optionChainData && (
            <div className="text-center py-12 text-slate-600 dark:text-slate-400">
              <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Enter an expiry date and click "Load Chain" to view option chain data</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OptionChainModal;
