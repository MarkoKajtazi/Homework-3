package com.example.demo.service;

import com.example.demo.model.Company;
import com.example.demo.model.CompanyTransaction;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public interface CompanyService {
    List<Company> getAll();
    Company getByCompanyCode(String code);
    List<CompanyTransaction> getTransactionByCompanyCode(String code);
    List<String> getAllCodes();
    void fetchAndSaveCompany();
}
