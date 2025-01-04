package com.example.demo.scheduling;
import com.example.demo.service.CSVDataImporter;
import com.example.demo.service.CompanyService;
import com.example.demo.service.CompanyTransactionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;

@Component
public class ScheduledTask {
    private final CompanyService companyService;
    CSVDataImporter csvDataImporter;
    RestTemplate restTemplate;

    public ScheduledTask(CompanyService companyService, CSVDataImporter csvDataImporter) {
        this.companyService = companyService;
        this.csvDataImporter = csvDataImporter;
        this.restTemplate = new RestTemplate();
    }

    @Scheduled(cron = "0 0 15 * * ?", zone = "Europe/Skopje")
    public void runTask() {
        System.out.println("Task executed at: " + LocalDateTime.now());

        String url = "http://127.0.0.1:5000/api/update";
        restTemplate.exchange(url, HttpMethod.GET, HttpEntity.EMPTY, Void.class);

        companyService.fetchAndSaveCompany();
        csvDataImporter.importCSVToDatabase();

        System.out.println("Task done at: " + LocalDateTime.now());
    }
}
