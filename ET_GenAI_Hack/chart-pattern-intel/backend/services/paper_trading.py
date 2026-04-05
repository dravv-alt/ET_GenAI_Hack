"""In-memory paper trading portfolio and ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class Position:
	symbol: str
	market: str
	quantity: float
	avg_price: float


@dataclass
class LedgerEntry:
	trade_id: int
	timestamp: str
	symbol: str
	market: str
	side: str
	quantity: float
	price: float
	realized_pnl: float
	cash_after: float


@dataclass
class PaperPortfolio:
	starting_cash: float
	cash: float
	positions: Dict[str, Position] = field(default_factory=dict)
	ledger: List[LedgerEntry] = field(default_factory=list)
	realized_pnl: float = 0.0
	next_trade_id: int = 1

	def reset(self, starting_cash: float) -> None:
		self.starting_cash = starting_cash
		self.cash = starting_cash
		self.positions.clear()
		self.ledger.clear()
		self.realized_pnl = 0.0
		self.next_trade_id = 1

	def _key(self, symbol: str, market: str) -> str:
		return f"{market}:{symbol}"

	def apply_trade(self, symbol: str, market: str, side: str, quantity: float, price: float) -> LedgerEntry:
		if quantity <= 0:
			raise ValueError("Quantity must be positive")
		if price <= 0:
			raise ValueError("Price must be positive")

		key = self._key(symbol, market)
		position = self.positions.get(key)
		realized = 0.0
		cost = quantity * price

		if side == "buy":
			if self.cash < cost:
				raise ValueError("Insufficient cash for trade")
			new_qty = quantity + (position.quantity if position else 0.0)
			new_avg = price
			if position and new_qty > 0:
				new_avg = ((position.avg_price * position.quantity) + cost) / new_qty
			self.positions[key] = Position(symbol=symbol, market=market, quantity=new_qty, avg_price=new_avg)
			self.cash -= cost
		elif side == "sell":
			if not position or position.quantity < quantity:
				raise ValueError("Insufficient position to sell")
			realized = (price - position.avg_price) * quantity
			self.realized_pnl += realized
			self.cash += cost
			remaining_qty = position.quantity - quantity
			if remaining_qty <= 0:
				self.positions.pop(key, None)
			else:
				self.positions[key] = Position(symbol=symbol, market=market, quantity=remaining_qty, avg_price=position.avg_price)
		else:
			raise ValueError("Side must be 'buy' or 'sell'")

		entry = LedgerEntry(
			trade_id=self.next_trade_id,
			timestamp=datetime.now(timezone.utc).isoformat(),
			symbol=symbol,
			market=market,
			side=side,
			quantity=quantity,
			price=price,
			realized_pnl=round(realized, 2),
			cash_after=round(self.cash, 2),
		)
		self.ledger.append(entry)
		self.next_trade_id += 1
		return entry

	def snapshot(self, latest_prices: Dict[str, float]) -> dict:
		positions = []
		unrealized = 0.0
		for key, pos in self.positions.items():
			last_price = latest_prices.get(key, pos.avg_price)
			pnl = (last_price - pos.avg_price) * pos.quantity
			unrealized += pnl
			positions.append({
				"symbol": pos.symbol,
				"market": pos.market,
				"quantity": round(pos.quantity, 4),
				"avg_price": round(pos.avg_price, 2),
				"last_price": round(last_price, 2),
				"unrealized_pnl": round(pnl, 2),
			})

		equity = self.cash + unrealized
		return {
			"cash": round(self.cash, 2),
			"equity": round(equity, 2),
			"realized_pnl": round(self.realized_pnl, 2),
			"unrealized_pnl": round(unrealized, 2),
			"positions": positions,
			"starting_cash": round(self.starting_cash, 2),
		}


PORTFOLIO = PaperPortfolio(starting_cash=100000.0, cash=100000.0)
