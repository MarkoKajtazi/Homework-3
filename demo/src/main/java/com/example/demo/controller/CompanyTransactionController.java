package com.example.demo.controller;

import com.example.demo.model.Company;
import com.example.demo.model.CompanyTransaction;
import com.example.demo.service.CSVDataImporter;
import com.example.demo.service.CompanyService;
import com.example.demo.service.CompanyTransactionService;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@RestController
@RequestMapping(value = "/api")
@Validated
@CrossOrigin(origins="*")
public class CompanyTransactionController {
    private final CompanyTransactionService companyTransactionService;
    private final CompanyService companyService;

    public CompanyTransactionController(CompanyTransactionService companyTransactionService, CompanyService companyService, CSVDataImporter csvDataImporter) {
        this.companyTransactionService = companyTransactionService;
        this.companyService = companyService;
        companyService.fetchAndSaveCompany();
        csvDataImporter.importCSVToDatabase();
    }

    @GetMapping("/all")
    public ResponseEntity<List<Company>> getAllData() {
        List<Company> transactions = companyService.getAll();
        return ResponseEntity.ok(transactions);
    }

    @GetMapping("/{id}")
    public ResponseEntity<CompanyTransaction> getDataById(@PathVariable Long id) {
        return ResponseEntity.ok(companyTransactionService.getDataById(id));
    }

    @GetMapping("/companies")
    public ResponseEntity<List<String>> getAllCompanies() {
        return ResponseEntity.ok(companyService.getAllCodes());
    }

    @GetMapping("/transactions/{code}")
    public ResponseEntity<List<CompanyTransaction>> getDataByCode(@PathVariable String code) {
        List<CompanyTransaction> transactions = companyService.getTransactionByCompanyCode(code);
        return ResponseEntity.ok(transactions);
    }

}
