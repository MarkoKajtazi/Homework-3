import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";

// Register Chart.js components and plugins
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    zoomPlugin
);

const tableHeaderStyle = {
    border: "1px solid #ccc",
    padding: "8px",
    color: "white",
    textAlign: "left",
    backgroundColor: "#555",
    position: "sticky",
    top: 0,
};

const tableCellStyle = {
    border: "1px solid #ccc",
    padding: "8px",
    color: "white",
    textAlign: "left",
};

const App = () => {
    const [companies, setCompanies] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState("");
    const [transactions, setTransactions] = useState([]);
    const [filteredTransactions, setFilteredTransactions] = useState([]);
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");
    const [visibleDatasets, setVisibleDatasets] = useState({
        sma20: true,
        sma50: true,
        ema20: true,
        ema50: true,
        bbMid: true,
        rsi: true,
        obv: true,
        momentum: true,
        buySignal: true,
        sellSignal: true,
    });

    // Fetch companies on mount
    useEffect(() => {
        fetch("http://localhost:8080/api/companies")
            .then((response) => response.json())
            .then((data) => setCompanies(data))
            .catch((err) => console.error("Error fetching companies:", err));
    }, []);

    const handleFetchTransactions = () => {
        if (!selectedCompany) {
            alert("Please select a company.");
            return;
        }

        fetch(`http://localhost:8080/api/transactions/${selectedCompany}`)
            .then((response) => response.json())
            .then((data) => {
                // Convert numeric fields properly, and define a new 'signal' field
                const parsedData = data.map((transaction) => {
                    const buySignal = transaction.buySignal === "True";
                    const sellSignal = transaction.sellSignal === "True";

                    return {
                        ...transaction,
                        lastPrice: parseFloat(transaction.lastPrice.replace(",", ".")),
                        min: parseFloat(transaction.min.replace(",", ".")),
                        max: parseFloat(transaction.max.replace(",", ".")),
                        averagePrice: parseFloat(transaction.averagePrice.replace(",", ".")),
                        percentageChange: parseFloat(transaction.percentageChange.replace(",", ".")),
                        sma20: parseFloat(transaction.sma20.replace(",", ".")),
                        sma50: parseFloat(transaction.sma50.replace(",", ".")),
                        ema20: parseFloat(transaction.ema20),
                        ema50: parseFloat(transaction.ema50),
                        bbMid: parseFloat(transaction.bbMid),
                        rsi: parseFloat(transaction.rsi),
                        obv: parseFloat(transaction.obv),
                        momentum: parseFloat(transaction.momentum),
                        buySignal,
                        sellSignal,
                        // Determine the signal based on buy/sell
                        signal: buySignal
                            ? "Buy"
                            : sellSignal
                                ? "Sell"
                                : "Hold",
                    };
                });

                // Sort by date ascending
                const sortedTransactions = parsedData.sort(
                    (a, b) => new Date(a.date) - new Date(b.date)
                );

                // If date filters are set, apply them
                if (fromDate && toDate) {
                    const from = new Date(fromDate);
                    const to = new Date(toDate);

                    const filtered = sortedTransactions.filter((t) => {
                        const txDate = new Date(t.date);
                        return txDate >= from && txDate <= to;
                    });
                    setFilteredTransactions(filtered);
                } else {
                    setFilteredTransactions(sortedTransactions);
                }

                setTransactions(sortedTransactions);
            })
            .catch((err) => console.error("Error fetching transactions:", err));
    };

    const handleReset = () => {
        setFromDate("");
        setToDate("");
        setFilteredTransactions(transactions);
    };

    const toggleDataset = (dataset) => {
        setVisibleDatasets((prev) => ({
            ...prev,
            [dataset]: !prev[dataset],
        }));
    };

    const formatDate = (date) => {
        const d = new Date(date);
        if (isNaN(d)) return "";
        const day = String(d.getDate()).padStart(2, "0");
        const month = String(d.getMonth() + 1).padStart(2, "0");
        const year = d.getFullYear();
        return `${day}.${month}.${year}`;
    };

    // Separate signals for the scatter plots
    const buySignals = filteredTransactions.filter((tx) => tx.signal === "Buy");
    const sellSignals = filteredTransactions.filter((tx) => tx.signal === "Sell");

    // (You could also filter for "Hold" signals if you'd like a separate dataset in the chart,
    // but here we only show buy/sell in the chart.)

    // Prepare chart data
    const chartData = {
        labels: filteredTransactions.map((transaction) => formatDate(transaction.date)),
        datasets: [
            {
                label: "Transaction Price",
                data: filteredTransactions.map((transaction) => transaction.lastPrice),
                borderColor: "rgba(75,192,192,1)",
                backgroundColor: "rgba(75,192,192,0.2)",
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: "rgba(75,192,192,1)",
                fill: false,
                yAxisID: "y",
            },
            visibleDatasets.sma20 && {
                label: "SMA 20",
                data: filteredTransactions.map((t) => t.sma20),
                borderColor: "rgba(255,99,132,1)",
                backgroundColor: "rgba(255,99,132,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "y",
            },
            visibleDatasets.sma50 && {
                label: "SMA 50",
                data: filteredTransactions.map((t) => t.sma50),
                borderColor: "rgba(153,102,255,1)",
                backgroundColor: "rgba(153,102,255,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "y",
            },
            visibleDatasets.ema20 && {
                label: "EMA 20",
                data: filteredTransactions.map((t) => t.ema20),
                borderColor: "rgba(54,162,235,1)",
                backgroundColor: "rgba(54,162,235,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "y",
            },
            visibleDatasets.ema50 && {
                label: "EMA 50",
                data: filteredTransactions.map((t) => t.ema50),
                borderColor: "rgba(255,159,64,1)",
                backgroundColor: "rgba(255,159,64,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "y",
            },
            visibleDatasets.bbMid && {
                label: "BB Mid",
                data: filteredTransactions.map((t) => t.bbMid),
                borderColor: "rgba(75, 192, 192, 0.6)",
                backgroundColor: "rgba(75, 192, 192, 0.1)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                borderDash: [5, 5],
                yAxisID: "y",
            },
            visibleDatasets.rsi && {
                label: "RSI",
                data: filteredTransactions.map((t) => t.rsi),
                borderColor: "rgba(255,206,86,1)",
                backgroundColor: "rgba(255,206,86,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "rsi",
            },
            visibleDatasets.obv && {
                label: "OBV",
                data: filteredTransactions.map((t) => t.obv),
                borderColor: "rgba(153,102,255,1)",
                backgroundColor: "rgba(153,102,255,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "obv",
            },
            visibleDatasets.momentum && {
                label: "Momentum",
                data: filteredTransactions.map((t) => t.momentum),
                borderColor: "rgba(255,99,132,1)",
                backgroundColor: "rgba(255,99,132,0.2)",
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                yAxisID: "momentum",
            },
            // Buy Signals
            visibleDatasets.buySignal && {
                label: "Buy Signal",
                data: buySignals.map((t) => ({
                    x: formatDate(t.date),
                    y: t.lastPrice,
                })),
                borderColor: "green",
                backgroundColor: "green",
                pointStyle: "triangle",
                pointRadius: 6,
                showLine: false,
                yAxisID: "y",
                type: "scatter",
            },
            // Sell Signals
            visibleDatasets.sellSignal && {
                label: "Sell Signal",
                data: sellSignals.map((t) => ({
                    x: formatDate(t.date),
                    y: t.lastPrice,
                })),
                borderColor: "red",
                backgroundColor: "red",
                pointStyle: "rectRot",
                pointRadius: 6,
                showLine: false,
                yAxisID: "y",
                type: "scatter",
            },
        ].filter(Boolean),
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false, // Let it fill the container height
        plugins: {
            legend: {
                position: "top",
                labels: {
                    color: "white",
                },
            },
            title: {
                display: true,
                text: `Transactions for ${selectedCompany}`,
                color: "white",
            },
            tooltip: {
                mode: "index",
                intersect: false,
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: "x",
                },
                zoom: {
                    wheel: {
                        enabled: true,
                    },
                    pinch: {
                        enabled: true,
                    },
                    mode: "x",
                },
            },
        },
        elements: {
            line: {
                tension: 0.2,
            },
        },
        scales: {
            x: {
                type: "category",
                grid: {
                    color: "rgba(255,255,255,0.1)",
                },
                ticks: {
                    color: "white",
                },
            },
            y: {
                type: "linear",
                position: "left",
                title: {
                    display: true,
                    text: "Price",
                    color: "white",
                },
                grid: {
                    color: "rgba(255,255,255,0.1)",
                },
                ticks: {
                    color: "white",
                },
            },
            rsi: {
                type: "linear",
                position: "right",
                title: {
                    display: true,
                    text: "RSI",
                    color: "white",
                },
                grid: {
                    drawOnChartArea: false,
                },
                ticks: {
                    color: "white",
                    beginAtZero: true,
                    max: 100,
                },
            },
            obv: {
                type: "linear",
                position: "right",
                title: {
                    display: true,
                    text: "OBV",
                    color: "white",
                },
                grid: {
                    drawOnChartArea: false,
                },
                ticks: {
                    color: "white",
                },
            },
            momentum: {
                type: "linear",
                position: "right",
                title: {
                    display: true,
                    text: "Momentum",
                    color: "white",
                },
                grid: {
                    drawOnChartArea: false,
                },
                ticks: {
                    color: "white",
                },
            },
        },
    };

    return (
        <div style={{ display: "flex", height: "100vh", backgroundColor: "#333" }}>
            {/* Sidebar */}
            <div
                style={{
                    width: "300px",
                    backgroundColor: "white",
                    padding: "20px",
                    boxSizing: "border-box",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-start",
                    alignItems: "flex-start",
                    height: "100vh",
                    overflowY: "auto",
                }}
            >
                <h1 style={{ color: "#333" }}>Macedonian Stocks Demo</h1>
                <div>
                    <select
                        name="companies"
                        id="companies"
                        onChange={(e) => setSelectedCompany(e.target.value)}
                        style={{
                            marginBottom: "10px",
                            padding: "10px",
                            fontSize: "16px",
                            width: "100%",
                        }}
                        value={selectedCompany}
                    >
                        <option value="">Select a Company</option>
                        {companies.map((company, index) => (
                            <option key={index} value={company}>
                                {company}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label>
                        From:{" "}
                        <input
                            type="date"
                            value={fromDate}
                            onChange={(e) => setFromDate(e.target.value)}
                            style={{ marginLeft: "10px", marginBottom: "10px" }}
                        />
                    </label>
                </div>
                <div style={{ marginTop: "10px" }}>
                    <label>
                        To:{" "}
                        <input
                            type="date"
                            value={toDate}
                            onChange={(e) => setToDate(e.target.value)}
                            style={{ marginLeft: "10px" }}
                        />
                    </label>
                </div>
                <button
                    onClick={handleFetchTransactions}
                    style={{
                        marginTop: "20px",
                        backgroundColor: "#333",
                        color: "white",
                        padding: "10px 20px",
                        fontSize: "16px",
                        border: "none",
                        cursor: "pointer",
                        width: "100%",
                    }}
                    disabled={!selectedCompany}
                >
                    View Transactions
                </button>
                <button
                    onClick={handleReset}
                    style={{
                        marginTop: "10px",
                        backgroundColor: "#555",
                        color: "white",
                        padding: "10px 20px",
                        fontSize: "16px",
                        border: "none",
                        cursor: "pointer",
                        width: "100%",
                    }}
                >
                    Reset
                </button>
                <div style={{ marginTop: "20px", width: "100%" }}>
                    <h3 style={{ color: "#333" }}>Toggle Datasets</h3>
                    {[
                        { key: "sma20", label: "SMA 20" },
                        { key: "sma50", label: "SMA 50" },
                        { key: "ema20", label: "EMA 20" },
                        { key: "ema50", label: "EMA 50" },
                        { key: "bbMid", label: "BB Mid" },
                        { key: "rsi", label: "RSI" },
                        { key: "obv", label: "OBV" },
                        { key: "momentum", label: "Momentum" },
                        { key: "buySignal", label: "Buy Signal" },
                        { key: "sellSignal", label: "Sell Signal" },
                    ].map((dataset) => (
                        <label
                            key={dataset.key}
                            style={{
                                color: "#333",
                                marginRight: "10px",
                                display: "flex",
                                alignItems: "center",
                                marginBottom: "5px",
                            }}
                        >
                            <input
                                type="checkbox"
                                checked={visibleDatasets[dataset.key]}
                                onChange={() => toggleDataset(dataset.key)}
                                style={{ marginRight: "5px" }}
                            />
                            {dataset.label}
                        </label>
                    ))}
                </div>
            </div>

            {/* Main Content (Chart + Table) */}
            <div
                style={{
                    flex: 1,
                    padding: "20px",
                    boxSizing: "border-box",
                    height: "100vh",
                    overflowY: "auto",
                }}
            >
                {/* Larger chart container */}
                <div style={{ height: "70vh", marginBottom: "20px" }}>
                    {filteredTransactions.length > 0 ? (
                        <Line data={chartData} options={chartOptions} />
                    ) : (
                        <p style={{ color: "white" }}>No transactions found.</p>
                    )}
                </div>

                {/* Table displaying transaction data, only if we have data */}
                {filteredTransactions.length > 0 && (
                    <div style={{ marginTop: "20px" }}>
                        <h2 style={{ color: "white", textAlign: "center" }}>
                            Transaction Data
                        </h2>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                            <tr>
                                <th style={tableHeaderStyle}>Date</th>
                                <th style={tableHeaderStyle}>Last Price</th>
                                <th style={tableHeaderStyle}>Min</th>
                                <th style={tableHeaderStyle}>Max</th>
                                <th style={tableHeaderStyle}>Average Price</th>
                                <th style={tableHeaderStyle}>% Change</th>
                                <th style={tableHeaderStyle}>Quantity</th>
                                <th style={tableHeaderStyle}>Turnover</th>
                                <th style={tableHeaderStyle}>Total Turnover</th>
                                <th style={tableHeaderStyle}>SMA 20</th>
                                <th style={tableHeaderStyle}>SMA 50</th>
                                <th style={tableHeaderStyle}>EMA 20</th>
                                <th style={tableHeaderStyle}>EMA 50</th>
                                <th style={tableHeaderStyle}>BB Mid</th>
                                <th style={tableHeaderStyle}>RSI</th>
                                <th style={tableHeaderStyle}>OBV</th>
                                <th style={tableHeaderStyle}>Momentum</th>
                                <th style={tableHeaderStyle}>Buy Signal</th>
                                <th style={tableHeaderStyle}>Sell Signal</th>
                                {/* New column showing the combined signal */}
                                <th style={tableHeaderStyle}>Signal</th>
                            </tr>
                            </thead>
                            <tbody>
                            {filteredTransactions.map((tx, idx) => (
                                <tr key={idx}>
                                    <td style={tableCellStyle}>{formatDate(tx.date)}</td>
                                    <td style={tableCellStyle}>{tx.lastPrice}</td>
                                    <td style={tableCellStyle}>{tx.min}</td>
                                    <td style={tableCellStyle}>{tx.max}</td>
                                    <td style={tableCellStyle}>
                                        {tx.averagePrice?.toFixed?.(2)}
                                    </td>
                                    <td style={tableCellStyle}>
                                        {tx.percentageChange?.toFixed?.(2)}%
                                    </td>
                                    <td style={tableCellStyle}>{tx.quantity}</td>
                                    <td style={tableCellStyle}>{tx.turnover}</td>
                                    <td style={tableCellStyle}>{tx.totalTurnover}</td>
                                    <td style={tableCellStyle}>{tx.sma20}</td>
                                    <td style={tableCellStyle}>{tx.sma50}</td>
                                    <td style={tableCellStyle}>{tx.ema20}</td>
                                    <td style={tableCellStyle}>{tx.ema50}</td>
                                    <td style={tableCellStyle}>{tx.bbMid}</td>
                                    <td style={tableCellStyle}>{tx.rsi}</td>
                                    <td style={tableCellStyle}>{tx.obv}</td>
                                    <td style={tableCellStyle}>{tx.momentum}</td>
                                    <td style={tableCellStyle}>
                                        {tx.buySignal ? "Yes" : "No"}
                                    </td>
                                    <td style={tableCellStyle}>
                                        {tx.sellSignal ? "Yes" : "No"}
                                    </td>
                                    {/* Display the new combined signal */}
                                    <td style={tableCellStyle}>{tx.signal}</td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default App;
