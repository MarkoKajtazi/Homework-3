package com.example.demo.service;

import com.example.demo.model.Company;
import com.example.demo.model.CompanyTransaction;
import com.example.demo.repository.CompanyRepository;
import com.example.demo.repository.CompanyTransactionRepository;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.FileReader;
import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Service
public class CSVDataImporter {
    @Autowired
    private CompanyTransactionRepository companyTransactionRepository;

    @Autowired
    private CompanyRepository companyRepository;

    @Transactional
    public void importCSVToDatabase() {
        companyTransactionRepository.deleteAll();
        List<Company> companies = companyRepository.findAll();

        for (Company company : companies) {
            String filePath = String.format("src/main/resources/combined_data_frame_%s.csv", company.getCode());
            try (CSVParser parser = CSVFormat.DEFAULT.withHeader().parse(new FileReader(filePath))) {
                for (CSVRecord record : parser) {
                    CompanyTransaction transaction = mapRecordToCompanyTransaction(record);
                    if (transaction != null) {
                        companyTransactionRepository.save(transaction);
                    }
                }

            } catch (IOException e) {
                throw new RuntimeException("Error reading CSV file: " + filePath, e);
            }
        }
    }

    private CompanyTransaction mapRecordToCompanyTransaction(CSVRecord record) {
        try {
            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");

            // Parse and validate fields
            String code = record.get("Company Code");
            String date = record.get("Date");
            String lastPrice = record.get("Price of last transaction (mkd)");
            String min = record.get("Min");
            String max = record.get("Max");
            String averagePrice = record.get("Average Price");
            String percentageChange = record.get("%change.");
            String quantity = record.get("Quantity");
            String turnover = record.get("Turnover in BEST in denars");
            String totalTurnover = record.get("Total turnover in denars");
            String sma20 = record.get("SMA_20");
            String sma50 = record.get("SMA_50");
            String ema20 = record.get("EMA_20");
            String ema50 = record.get("EMA_50");
            String bbMid = record.get("BB_Mid");
            String rsi = record.get("RSI");
            String obv = record.get("OBV");
            String momentum = record.get("Momentum");
            String buySignal = record.get("Buy_Signal");
            String sellSignal = record.get("Sell_Signal");

            Company company = companyRepository.getReferenceById(code);
            CompanyTransaction companyTransaction = new CompanyTransaction(date, lastPrice, min, max, averagePrice, percentageChange, quantity, turnover, totalTurnover,
                    sma20, sma50, ema20, ema50, bbMid, rsi, obv, momentum, buySignal, sellSignal, company);

            company.addTransaction(companyTransaction);

            return companyTransaction;
        } catch (IllegalArgumentException e) {
            System.err.println("Skipping invalid record: " + record);
            return null;
        }
    }

    private Double parseDouble(String value) {
        return value == null || value.isEmpty() ? null : Double.valueOf(value);
    }

    private Long parseLong(String value) {
        return value == null || value.isEmpty() ? null : Long.valueOf(value);
    }

    private Boolean parseBoolean(String value) {
        return value != null && value.equalsIgnoreCase("true");
    }
}