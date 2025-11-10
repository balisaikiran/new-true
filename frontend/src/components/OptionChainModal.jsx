import { useState, useEffect } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { X, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OptionChainModal = ({ stock, token, onClose }) => {
  const [expiry, setExpiry] = useState("");
  const [optionChainData, setOptionChainData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parsedData, setParsedData] = useState([]);

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
        parseOptionChainData(response.data.data);
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

  const parseOptionChainData = (data) => {
    if (!data || !data.Records || !Array.isArray(data.Records)) {
      setParsedData([]);
      return;
    }

    // Parse the option chain data
    // Based on actual data structure: [symbol, expiry, null, call_OI, call_LTP, zeros..., strike, zeros..., put_bid, put_ask, put_LTP, put_volume]
    const parsed = [];
    const strikeMap = new Map();

    data.Records.forEach((record) => {
      if (!Array.isArray(record) || record.length < 11) return;

      // Index 11 is the strike price (1200, 1240, 1280, 1300, etc.)
      const strike = record[11];
      if (!strike || typeof strike !== 'number') return;

      // Call option data (before strike)
      const callOI = record[3] !== null && record[3] !== undefined ? record[3] : null;
      const callLTP = record[4] !== null && record[4] !== undefined ? record[4] : null;
      
      // Try to find call bid/ask (usually zeros in this API, but check indices 5-10)
      let callBid = null, callAsk = null, callVolume = null;
      for (let i = 5; i < 11; i++) {
        if (record[i] && typeof record[i] === 'number' && record[i] > 0) {
          if (!callBid) callBid = record[i];
          else if (!callAsk) callAsk = record[i];
          else if (!callVolume && record[i] > 1000) callVolume = record[i];
        }
      }

      // Put option data (after strike)
      // Based on sample: indices 16-17 are large numbers (bid/ask), 18 is small decimal (LTP), 19 is large number (volume)
      const putBid = record[16] !== null && record[16] !== undefined && record[16] > 0 ? record[16] : null;
      const putAsk = record[17] !== null && record[17] !== undefined && record[17] > 0 ? record[17] : null;
      const putLTP = record[18] !== null && record[18] !== undefined && record[18] > 0 ? record[18] : null;
      const putVolume = record[19] !== null && record[19] !== undefined && record[19] > 0 ? record[19] : null;
      
      // Try to find put OI (might be in other indices)
      let putOI = null;
      for (let i = 12; i < 16; i++) {
        if (record[i] && typeof record[i] === 'number' && record[i] > 0 && record[i] < 1000000) {
          putOI = record[i];
          break;
        }
      }

      // Store in map (handle duplicates by merging)
      if (strikeMap.has(strike)) {
        const existing = strikeMap.get(strike);
        strikeMap.set(strike, {
          strike,
          callOI: callOI !== null ? callOI : existing.callOI,
          callLTP: callLTP !== null ? callLTP : existing.callLTP,
          callBid: callBid !== null ? callBid : existing.callBid,
          callAsk: callAsk !== null ? callAsk : existing.callAsk,
          callVolume: callVolume !== null ? callVolume : existing.callVolume,
          putOI: putOI !== null ? putOI : existing.putOI,
          putLTP: putLTP !== null ? putLTP : existing.putLTP,
          putBid: putBid !== null ? putBid : existing.putBid,
          putAsk: putAsk !== null ? putAsk : existing.putAsk,
          putVolume: putVolume !== null ? putVolume : existing.putVolume,
        });
      } else {
        strikeMap.set(strike, {
          strike,
          callOI,
          callLTP,
          callBid,
          callAsk,
          callVolume,
          putOI,
          putLTP,
          putBid,
          putAsk,
          putVolume,
        });
      }
    });

    // Convert to array and sort by strike price
    const sorted = Array.from(strikeMap.values()).sort((a, b) => a.strike - b.strike);
    setParsedData(sorted);
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
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                {parsedData.length > 0 ? (
                  <Table>
                    <TableHeader className="sticky top-0 bg-slate-100 dark:bg-slate-800 z-10">
                      <TableRow>
                        <TableHead className="text-center font-bold text-blue-600 dark:text-blue-400">CALLS</TableHead>
                        <TableHead className="text-center">OI</TableHead>
                        <TableHead className="text-center">LTP</TableHead>
                        <TableHead className="text-center">Bid</TableHead>
                        <TableHead className="text-center">Ask</TableHead>
                        <TableHead className="text-center">Volume</TableHead>
                        <TableHead className="text-center font-bold border-l-2 border-r-2 border-slate-300 dark:border-slate-700">STRIKE</TableHead>
                        <TableHead className="text-center font-bold text-red-600 dark:text-red-400">PUTS</TableHead>
                        <TableHead className="text-center">OI</TableHead>
                        <TableHead className="text-center">LTP</TableHead>
                        <TableHead className="text-center">Bid</TableHead>
                        <TableHead className="text-center">Ask</TableHead>
                        <TableHead className="text-center">Volume</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {parsedData.map((row, idx) => (
                        <TableRow key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-900">
                          <TableCell className="text-right font-medium text-blue-600 dark:text-blue-400">
                            {row.callLTP !== null && row.callLTP !== undefined ? row.callLTP.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-right text-slate-600 dark:text-slate-400">
                            {row.callOI !== null && row.callOI !== undefined ? row.callOI.toLocaleString() : '-'}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {row.callLTP !== null && row.callLTP !== undefined ? row.callLTP.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-right text-green-600 dark:text-green-400">
                            {row.callBid !== null && row.callBid !== undefined && row.callBid > 0 ? row.callBid.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-right text-red-600 dark:text-red-400">
                            {row.callAsk !== null && row.callAsk !== undefined && row.callAsk > 0 ? row.callAsk.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-right text-slate-500 dark:text-slate-400">
                            {row.callVolume !== null && row.callVolume !== undefined ? row.callVolume.toLocaleString() : '-'}
                          </TableCell>
                          <TableCell className="text-center font-bold border-l-2 border-r-2 border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
                            {row.strike}
                          </TableCell>
                          <TableCell className="text-left font-medium text-red-600 dark:text-red-400">
                            {row.putLTP !== null && row.putLTP !== undefined ? row.putLTP.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-left text-slate-600 dark:text-slate-400">
                            {row.putOI !== null && row.putOI !== undefined ? row.putOI.toLocaleString() : '-'}
                          </TableCell>
                          <TableCell className="text-left font-medium">
                            {row.putLTP !== null && row.putLTP !== undefined ? row.putLTP.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-left text-green-600 dark:text-green-400">
                            {row.putBid !== null && row.putBid !== undefined && row.putBid > 0 ? row.putBid.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-left text-red-600 dark:text-red-400">
                            {row.putAsk !== null && row.putAsk !== undefined && row.putAsk > 0 ? row.putAsk.toFixed(2) : '-'}
                          </TableCell>
                          <TableCell className="text-left text-slate-500 dark:text-slate-400">
                            {row.putVolume !== null && row.putVolume !== undefined ? row.putVolume.toLocaleString() : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="p-4">
                    <pre className="text-xs bg-slate-50 dark:bg-slate-900 p-4 rounded-lg overflow-auto">
                      {JSON.stringify(optionChainData, null, 2)}
                    </pre>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                      Unable to parse option chain data. Showing raw data above.
                    </p>
                  </div>
                )}
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
