package com.example.demo.service;

import com.example.demo.model.CompanyTransaction;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public interface CompanyTransactionService {
    public List<CompanyTransaction> getAllData();
    public CompanyTransaction getDataById(Long id);
}
