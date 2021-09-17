# finance
### An application via which you can manage portfolios of stocks, check stock prices, and buy/sell stocks by querying IEX for prices.

![](/static/finance.gif)

## Description

Through the use of IEX's API, the user obtain stock quotes by providing a stock's ticker symbol. After registering for an account, a user can log in and is given a fake $10,000 to spend. This investment can be used to buy/sell stocks and observe their values fluctuate over time since IEX provides us with real time prices.

* **Index:** The homepage displays an HTML table of the user's investments which by default starts with $10,000. Afterwards, the table displays whichever stocks the user owns, the current cash balance, and the total portfolio value.

* **Quote:** The quote page allows a user to look up a stock's current price. 

* **Buy:** The buy page allows a user to purchase stocks.

* **Sell:** The sell page allows a user to sell only their stocks.

* **Graph:** The graph route implements Chart.js to display a pie chart of the investment allocation of the user's portfolio. 

* **History:** The history route displays a buying/selling history of all stocks purchased and sold, and allows the user to sort the history. 