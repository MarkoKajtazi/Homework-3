package com.example.demo.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.*;

import java.io.Serializable;
import java.util.Date;

@Data
@Entity
@Table(name = "CompanyTransaction")
@JsonIgnoreProperties({"company"})
public class CompanyTransaction implements Serializable {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    private Company company;

    private String date;

    private String lastPrice;

    private String min;

    private String max;

    private String averagePrice;

    private String percentageChange;

    private String quantity;

    private String turnover;

    private String totalTurnover;

    private String sma20;

    private String sma50;

    private String ema20;

    private String ema50;

    private String bbMid;

    private String rsi;

    private String obv;

    private String momentum;

    private String buySignal;

    private String sellSignal;


    public CompanyTransaction(String date, String lastPrice, String min, String max, String averagePrice, String percentageChange, String quantity, String turnover, String totalTurnover, String sma20, String sma50, String ema20, String ema50, String bbMid, String rsi, String obv, String momentum, String buySignal, String sellSignal, Company company) {
        this.company = company;
        this.date = date;
        this.lastPrice = lastPrice;
        this.min = min;
        this.max = max;
        this.averagePrice = averagePrice;
        this.percentageChange = percentageChange;
        this.quantity = quantity;
        this.turnover = turnover;
        this.totalTurnover = totalTurnover;
        this.sma20 = sma20;
        this.sma50 = sma50;
        this.ema20 = ema20;
        this.ema50 = ema50;
        this.bbMid = bbMid;
        this.rsi = rsi;
        this.obv = obv;
        this.momentum = momentum;
        this.buySignal = buySignal;
        this.sellSignal = sellSignal;
    }

    public CompanyTransaction() {}

    public Long getId() {
        return id;
    }

    public Company getCompany() {
        return company;
    }

    public String getDate() {
        return date;
    }

    public String getLastPrice() {
        return lastPrice;
    }

    public String getMin() {
        return min;
    }

    public String getMax() {
        return max;
    }

    public String getAveragePrice() {
        return averagePrice;
    }

    public String getPercentageChange() {
        return percentageChange;
    }

    public String getQuantity() {
        return quantity;
    }

    public String getTurnover() {
        return turnover;
    }

    public String getTotalTurnover() {
        return totalTurnover;
    }

    public String getSma20() {
        return sma20;
    }

    public String getSma50() {
        return sma50;
    }

    public String getEma20() {
        return ema20;
    }

    public String getEma50() {
        return ema50;
    }

    public String getBbMid() {
        return bbMid;
    }

    public String getRsi() {
        return rsi;
    }

    public String getObv() {
        return obv;
    }

    public String getMomentum() {
        return momentum;
    }

    public String getBuySignal() {
        return buySignal;
    }

    public String getSellSignal() {
        return sellSignal;
    }
}
