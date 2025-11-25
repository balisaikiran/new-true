import { useState, useEffect } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { X, Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
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

  const getLotSize = (symbol) => {
    // Common lot sizes
    const lotSizes = {
      'NIFTY': 50,
      'BANKNIFTY': 15,
    };
    // Default lot size for stocks is 500
    return lotSizes[symbol] || 500;
  };

  const parseOptionChainData = (data) => {
    if (!data || !data.Records || !Array.isArray(data.Records)) {
      setParsedData([]);
      return;
    }

    // Parse the option chain data based on TrueData API structure
    // Structure: [symbol, expiry, call_timestamp, call_OI, call_LTP, call_bid, call_bid_qty, call_ask, call_ask_qty, call_vol, call_pOI, strike, put_bid, put_bid_qty, put_ask, put_ask_qty, put_OI, put_pOI, put_LTP, put_vol, put_timestamp]
    const parsed = [];
    const strikeMap = new Map();

    // Get symbol and lot size from first record
    const symbol = data.Records[0] && data.Records[0][0] ? data.Records[0][0] : 'NIFTY';
    const lotSize = getLotSize(symbol);

    data.Records.forEach((record) => {
      if (!Array.isArray(record) || record.length < 21) return;

      // Index 11 is the strike price
      const strike = record[11];
      if (!strike || typeof strike !== 'number') return;

      // Call option data (indices 3-10)
      const callOIRaw = record[3] !== null && record[3] !== undefined ? record[3] : null;
      const callLTP = record[4] !== null && record[4] !== undefined ? record[4] : null;
      const callBid = record[5] !== null && record[5] !== undefined && record[5] > 0 ? record[5] : null;
      const callBidQty = record[6] !== null && record[6] !== undefined ? record[6] : null;
      const callAsk = record[7] !== null && record[7] !== undefined && record[7] > 0 ? record[7] : null;
      const callAskQty = record[8] !== null && record[8] !== undefined ? record[8] : null;
      const callVolRaw = record[9] !== null && record[9] !== undefined ? record[9] : null;
      
      // Put option data (indices 12-19)
      const putBid = record[12] !== null && record[12] !== undefined && record[12] > 0 ? record[12] : null;
      const putBidQty = record[13] !== null && record[13] !== undefined ? record[13] : null;
      const putAsk = record[14] !== null && record[14] !== undefined && record[14] > 0 ? record[14] : null;
      const putAskQty = record[15] !== null && record[15] !== undefined ? record[15] : null;
      const putOIRaw = record[16] !== null && record[16] !== undefined ? record[16] : null;
      const putLTP = record[18] !== null && record[18] !== undefined && record[18] > 0 ? record[18] : null;
      const putVolRaw = record[19] !== null && record[19] !== undefined ? record[19] : null;
      
      // Convert OI and Volume from lot-size-multiplied to NSE-equivalent
      // TrueData provides: OI * lot_size, so divide by lot_size to get NSE value
      const callOI = callOIRaw !== null && lotSize > 0 ? callOIRaw / lotSize : null;
      const callVolume = callVolRaw !== null && lotSize > 0 ? callVolRaw / lotSize : null;
      const putOI = putOIRaw !== null && lotSize > 0 ? putOIRaw / lotSize : null;
      const putVolume = putVolRaw !== null && lotSize > 0 ? putVolRaw / lotSize : null;

      // Store in map (handle duplicates by merging)
      if (strikeMap.has(strike)) {
        const existing = strikeMap.get(strike);
        strikeMap.set(strike, {
          strike,
          callOI: callOI !== null ? callOI : existing.callOI,
          callLTP: callLTP !== null ? callLTP : existing.callLTP,
          callBid: callBid !== null ? callBid : existing.callBid,
          callBidQty: callBidQty !== null ? callBidQty : existing.callBidQty,
          callAsk: callAsk !== null ? callAsk : existing.callAsk,
          callAskQty: callAskQty !== null ? callAskQty : existing.callAskQty,
          callVolume: callVolume !== null ? callVolume : existing.callVolume,
          putOI: putOI !== null ? putOI : existing.putOI,
          putLTP: putLTP !== null ? putLTP : existing.putLTP,
          putBid: putBid !== null ? putBid : existing.putBid,
          putBidQty: putBidQty !== null ? putBidQty : existing.putBidQty,
          putAsk: putAsk !== null ? putAsk : existing.putAsk,
          putAskQty: putAskQty !== null ? putAskQty : existing.putAskQty,
          putVolume: putVolume !== null ? putVolume : existing.putVolume,
        });
      } else {
        strikeMap.set(strike, {
          strike,
          callOI,
          callLTP,
          callBid,
          callBidQty,
          callAsk,
          callAskQty,
          callVolume,
          putOI,
          putLTP,
          putBid,
          putBidQty,
          putAsk,
          putAskQty,
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
