import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
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
} from "chart.js";

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const List = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { companyCode } = location.state || {};
    const [transactions, setTransactions] = useState([]);
    const [filteredTransactions, setFilteredTransactions] = useState([]);
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");

    useEffect(() => {
        if (companyCode) {
            fetch(`http://localhost:8080/api/transactions/${companyCode}`)
                .then((response) => response.json())
                .then((data) => {
                    const sortedTransactions = data.sort(
                        (a, b) => new Date(a.date) - new Date(b.date)
                    );
                    setTransactions(sortedTransactions);
                    setFilteredTransactions(sortedTransactions);
                });
        }
    }, [companyCode]);

    const handleFilter = () => {
        if (fromDate && toDate) {
            const from = new Date(fromDate);
            const to = new Date(toDate);

            const filtered = transactions.filter((transaction) => {
                const transactionDate = new Date(transaction.date);
                return transactionDate >= from && transactionDate <= to;
            });

            setFilteredTransactions(filtered);
        } else {
            alert("Please select both from-date and to-date.");
        }
    };

    const handleResetFilter = () => {
        setFromDate("");
        setToDate("");
        setFilteredTransactions(transactions);
    };

    const formatDate = (date) => {
        const d = new Date(date);
        const day = d.getDate().toString().padStart(2, "0");
        const month = (d.getMonth() + 1).toString().padStart(2, "0");
        const year = d.getFullYear();
        return `${day}.${month}.${year}`;
    };

    const chartData = {
        labels: filteredTransactions.map((transaction) =>
            formatDate(transaction.date)
        ),
        datasets: [
            {
                label: "Transaction Amount",
                data: filteredTransactions.map((transaction) => transaction.amount),
                borderColor: "rgba(75,192,192,1)",
                backgroundColor: "rgba(75,192,192,0.2)",
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: "top",
            },
            title: {
                display: true,
                text: `Transactions for ${companyCode}`,
            },
        },
    };

    return (
        <div>
            <h1>Transactions for {companyCode}</h1>

            {/* Back Button */}
            <button onClick={() => navigate("/")} style={{ marginBottom: "20px" }}>
                Back to Select Company
            </button>

            {/* Date Filters */}
            <div style={{ marginBottom: "20px" }}>
                <label>
                    From:{" "}
                    <input
                        type="date"
                        value={fromDate}
                        onChange={(e) => setFromDate(e.target.value)}
                    />
                </label>
                <label style={{ marginLeft: "10px" }}>
                    To:{" "}
                    <input
                        type="date"
                        value={toDate}
                        onChange={(e) => setToDate(e.target.value)}
                    />
                </label>
                <button onClick={handleFilter} style={{ marginLeft: "10px" }}>
                    Filter
                </button>
                {/* Reset Button */}
                <button onClick={handleResetFilter} style={{ marginLeft: "10px" }}>
                    Reset Filter
                </button>
            </div>

            {/* Line Chart */}
            {filteredTransactions.length > 0 ? (
                <div>
                    <Line data={chartData} options={chartOptions} />
                    <ul>
                        {filteredTransactions.map((transaction) => (
                            <li key={transaction.id}>
                                Date: {formatDate(transaction.date)} |
                                Amount: {transaction.amount}
                            </li>
                        ))}
                    </ul>
                </div>
            ) : (
                <p>No transactions found.</p>
            )}
        </div>
    );
};

export default List;
