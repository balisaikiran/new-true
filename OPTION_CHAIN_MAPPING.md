# Option Chain Data Mapping - TrueData API

## Overview
This document explains the correct mapping of TrueData API option chain data structure and how to handle lot size calculations.

## TrueData API Structure

The option chain data comes as a `Records` array, where each record is a list with 21 elements:

### Record Structure (21 elements)

| Index | Field Name | Description | Example |
|-------|------------|-------------|---------|
| 0 | Symbol | Stock/Index symbol | "NIFTY", "RELIANCE" |
| 1 | Expiry Date | Expiry in DD-MM-YYYY format | "02-12-2025" |
| 2 | Call Timestamp | Call data timestamp | "25-11-2025 11:42:13" |
| 3 | Call OI | Call Open Interest (× lot size) | 0, 611700 |
| 4 | Call LTP | Call Last Traded Price | 2420.75 |
| 5 | Call Bid | Call Bid Price | 2248.6 |
| 6 | Call Bid Qty | Call Bid Quantity | 750 |
| 7 | Call Ask | Call Ask Price | 2289.0 |
| 8 | Call Ask Qty | Call Ask Quantity | 750 |
| 9 | Call Volume | Call Volume (× lot size) or Call pOI | 675, 528525 |
| 10 | Call pOI | Call Previous OI or Call Volume | 675 |
| 11 | **Strike Price** | Strike Price | 23750.0, 1160 |
| 12 | Put Bid | Put Bid Price | 1.85 |
| 13 | Put Bid Qty | Put Bid Quantity | 3600 |
| 14 | Put Ask | Put Ask Price | 1.9 |
| 15 | Put Ask Qty | Put Ask Quantity | 10800 |
| 16 | Put OI | Put Open Interest (× lot size) | 611700 |
| 17 | Put pOI | Put Previous OI | 347025 |
| 18 | Put LTP | Put Last Traded Price | 1.9 |
| 19 | Put Volume | Put Volume (× lot size) | 528525 |
| 20 | Put Timestamp | Put data timestamp | "25-11-2025 11:42:13" |

## Lot Size Handling

**Important**: TrueData API provides OI and Volume values that are **already multiplied by lot size**.

### Lot Sizes by Symbol

| Symbol | Lot Size |
|--------|----------|
| NIFTY | 50 |
| BANKNIFTY | 15 |
| Stocks (default) | 500 |

### Conversion Formula

To get NSE-equivalent values (matching NSE website):
```
NSE_OI = TrueData_OI / lot_size
NSE_Volume = TrueData_Volume / lot_size
```

### Example

For strike 1160 with lot size 500:
- TrueData Put OI: 15000
- NSE-equivalent Put OI: 15000 / 500 = 30
- This matches NSE website which shows OI = 30

## Implementation

### Backend (`backend/server.py`)

The `parse_option_chain_record()` function handles the mapping:

```python
def parse_option_chain_record(record: List[Any], symbol: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single option chain record based on TrueData API structure.
    Automatically handles lot size conversion.
    """
    lot_size = get_lot_size(symbol)
    
    # Extract raw values
    call_oi_raw = record[3]
    call_ltp = record[4]
    # ... etc
    
    # Convert to NSE-equivalent
    call_oi = call_oi_raw / lot_size if call_oi_raw and lot_size > 0 else None
    # ... etc
```

### Frontend (`frontend/src/components/OptionChainModal.jsx`)

The `parseOptionChainData()` function handles the mapping:

```javascript
const getLotSize = (symbol) => {
  const lotSizes = {
    'NIFTY': 50,
    'BANKNIFTY': 15,
  };
  return lotSizes[symbol] || 500;
};

// In parseOptionChainData:
const lotSize = getLotSize(symbol);
const callOI = callOIRaw !== null && lotSize > 0 ? callOIRaw / lotSize : null;
const callVolume = callVolRaw !== null && lotSize > 0 ? callVolRaw / lotSize : null;
// ... etc
```

## IV Calculation

IV (Implied Volatility) is calculated from option prices (LTP) using Black-Scholes model:

- **Call IV**: Calculated from `Call LTP` (index 4)
- **Put IV**: Calculated from `Put LTP` (index 18)
- Uses ATM (At-The-Money) options (strikes closest to spot price)
- Returns average IV from multiple ATM options

## Reference

- NSE Option Chain: https://www.nseindia.com/get-quotes/derivatives?symbol=RELIANCE
- TrueData API provides values multiplied by lot size
- Divide by lot size to match NSE website values

## Notes

1. **OI and Volume**: Always divide by lot size to get NSE-equivalent values
2. **Prices**: LTP, Bid, Ask are already in correct format (no conversion needed)
3. **Strike Price**: Index 11 contains the strike price
4. **Timestamps**: Available at indices 2 (call) and 20 (put)
5. **Missing Data**: Some fields may be null/0, handle gracefully

