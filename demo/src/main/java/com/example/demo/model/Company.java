package com.example.demo.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "Company")
public class Company {
    @Id
    private String code;

    @OneToMany(mappedBy = "company")
    List<CompanyTransaction> transactions;

    public Company(String code) {
        this.code = code;
        transactions = new ArrayList<>();
    }

    public Company() {}

    public String getCode() {
        return code;
    }

    public List<CompanyTransaction> getTransactions() {
        return transactions;
    }

    public CompanyTransaction addTransaction(CompanyTransaction transaction) {
        transactions.add(transaction);
        return transaction;
    }

    public void removeTransaction(CompanyTransaction transaction) {
        transactions.remove(transaction);
    }

    public void setCode(String code) {
        this.code = code;
    }
}
