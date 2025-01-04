import React, {useState, useEffect} from "react";
import {useNavigate} from "react-router-dom";

const Home = () => {
    const [state, setState] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState("");
    const navigate = useNavigate();


    useEffect(() => {
        fetch("http://localhost:8080/api/companies")
            .then((response) => response.json())
            .then((data) => {
                setState(data);
            });
    }, []);

    const handleButtonClick = () => {
        if (selectedCompany) {
            navigate("/list", { state: { companyCode: selectedCompany } });
        } else {
            alert("Please select a company code.");
        }
    };

    return (
        <div>
            <h1>Macedonian Stocks Demo</h1>
            <div>
                <select name="companies" id="companies" onChange={(e) => setSelectedCompany(e.target.value)}>
                    <option value="">Select a Company</option>
                    {state.map((company, index) => (
                        <option key={index} value={company}>
                            {company}
                        </option>
                    ))}
                </select>
                <button onClick={handleButtonClick}>View Transactions</button>
            </div>
        </div>
    );
};

export default Home;
