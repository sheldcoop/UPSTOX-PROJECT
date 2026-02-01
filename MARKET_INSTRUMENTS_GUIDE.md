# Market Instruments Guide - Upstox Platform

This document provides a detailed breakdown of the instrument categories, codes, and counts available in the Upstox database. It serves as a reference to understand "Signal vs Noise" in the market data.

## 📊 Summary of Assets

| Category | Count | Description |
| :--- | :--- | :--- |
| **Total Instruments** | **207,764** | All listed instruments |
| **Clean Equity** | **7,660** | Common Stocks (NSE + BSE) |
| **SME Stocks** | **814** | Small & Medium Enterprises (NSE + BSE) |
| **Derivatives** | **186,201** | Options & Futures Contracts |
| **Debt & Bonds** | **6,791** | Govt Bonds, Corp Bonds, Fixed Income |
| **Gold** | **3,955** | Sovereign Gold Bonds (SGB) |
| **Indices** | **203** | Market Indices (Nifty 50, etc.) |
| **ETFs** | **109** | Exchange Traded Funds |

---

## 🏢 NSE - National Stock Exchange (Equity)

**Total Frontend Visible: ~2,967**

| Code | Type | Count | Description |
| :--- | :--- | :--- | :--- |
| **EQ** | Equity | **2,411** | **Mainboard Stocks**. The standard common stocks (RELIANCE, TCS). Liquid and safe for most traders. |
| **BE** | Restricted | **97** | **Book Entry / Trade-to-Trade**. Stocks under surveillance or illiquid. Must be taken delivery of (No Intraday). |
| **SM** | SME | **459** | **Small & Medium Enterprise**. Emerging companies. High risk, high lot sizes. |
| **BZ** | Restricted | **34** | **Z Category**. Blacklisted/Non-compliant companies. Extremely high risk. |
| **SG** | Gold | **3,955** | **Sovereign Gold Bonds**. Govt-backed gold securities. (Visible in "Gold" tab). |
| **N1** | ETF | **109** | **ETFs**. NiftyBees, GoldBees, LiquidBees. (Visible in "ETFs" tab). |

---

## 🏛️ BSE - Bombay Stock Exchange (Equity)

**Total Frontend Visible: ~4,693**

| Code | Group | Count | Description |
| :--- | :--- | :--- | :--- |
| **A** | Group A | **730** | **Top Stocks**. Most liquid and highly traded companies on BSE. |
| **B** | Group B | **1,614** | **Mid/Small Cap**. Normal liquidity, standard settlement. |
| **X** | Group X | **1,358** | **Penny/Illiquid**. Stocks listed on BSE only, often very low volume. |
| **XT** | Group XT | **406** | **Trade-to-Trade**. Techincally X group but strictly delivery based (No Intraday). |
| **M**  | SME | **355** | **BSE SME**. Small & Medium Enterprises on BSE. |
| **T** | T2T | **99** | **Trade-to-Trade**. Segment under surveillance. Delivery only. |
| **Z** | Z Group | **75** | **Danger Zone**. Companies with issues (listing agreement violations, etc.). |
| **P** | P Group | **56** | **Physical**. Shares that might still be in physical certificate form (rare). |
| **F** | Debt | **6,603** | **Fixed Income**. Corporate bonds and debentures. (Visible in "Debt" tab). |
| **G** | G-Sec | **1,101** | **Govt Securities**. Government bonds. (Visible in "Debt" tab). |

---

## ⚡ Derivatives (F&O)

Derived from **~258** Underlying Symbols (NIFTY, BANKNIFTY, RELIANCE, etc.). The dashboard uses a dedicated "Options & Futures" widget for this.

| Type | Count | Description |
| :--- | :--- | :--- |
| **Call Options (CE)** | **92,610** | Right to BUY. |
| **Put Options (PE)** | **92,498** | Right to SELL. |
| **Futures (FUT)** | **1,093** | Forward contracts expiring at month end. |

---

## 📉 Indices & ETFs

| Type | Count | Description |
| :--- | :--- | :--- |
| **INDICES** | **203** | Market benchmarks. (See "Indices" tab). |
| **ETFs** | **109** | Tradeable funds. (See "ETFs" tab). |

---

## 🔍 Dashboard Tabs Structure

The "Data Downloads" page is organized into 7 distinct tabs to handle the different "universes" of data:

1.  **NSE EQ**: Mainboard Stocks (**EQ, BE, BZ**) only. No SMEs.
2.  **BSE EQ**: Mainboard Stocks (**A, B, X, XT, T, Z, P**) only. No SMEs.
3.  **SME**: Dedicated home for High-Risk/High-Growth stocks (**NSE 'SM' + BSE 'M'**).
4.  **Debt**: Fixed Income & Govt Bonds (**F, G, GB, GS**).
5.  **Gold**: Sovereign Gold Bonds (**SG**) only.
6.  **Indices**: Market Indices like Nifty 50.
7.  **ETFs**: Exchange Traded Funds.

