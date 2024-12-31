package com.example.demo.service.impl;

import com.example.demo.model.CompanyTransaction;
import com.example.demo.repository.CompanyTransactionRepository;
import com.example.demo.service.CompanyTransactionService;
import org.hibernate.annotations.Fetch;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class CompanyTransactionServiceImpl implements CompanyTransactionService {
    @Autowired
    private CompanyTransactionRepository companyTransactionRepository;

    @Override
    public List<CompanyTransaction> getAllData() {
        return companyTransactionRepository.findAll();
    }

    @Override
    public CompanyTransaction getDataById(Long id) {
        return companyTransactionRepository.findById(id).orElse(null);
    }
}
