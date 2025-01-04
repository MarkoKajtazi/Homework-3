package com.example.demo.service.impl;

import com.example.demo.model.Company;
import com.example.demo.model.CompanyTransaction;
import com.example.demo.repository.CompanyRepository;
import com.example.demo.service.CompanyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class CompanyServiceImpl implements CompanyService {
    @Autowired
    private CompanyRepository companyRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public List<Company> getAll() {
        return companyRepository.findAll();
    }

    @Override
    public Company getByCompanyCode(String code) {
        return companyRepository.getReferenceById(code);
    }

    @Override
    public List<CompanyTransaction> getTransactionByCompanyCode(String code) {
        return companyRepository.getReferenceById(code).getTransactions();
    }

    @Override
    public List<String> getAllCodes() {
        return companyRepository.findAll().stream().map(Company::getCode).collect(Collectors.toList());
    }

    public void fetchAndSaveCompany() {
        List<String> codes = restTemplate.getForObject("http://127.0.0.1:5000/api/companies", List.class);
        for (String code : codes) {
            Company company = new Company(code);
            companyRepository.save(company);
        }
    }
}
