package com.example.sentiment;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVRecord;
import org.springframework.context.annotation.Bean;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import com.vader.sentiment.analyzer.SentimentAnalyzer;
import com.vader.sentiment.analyzer.SentimentPolarities;

import java.io.ByteArrayInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Function;

@SpringBootApplication(proxyBeanMethods = false)
public class SentimentFunction {

    private final ObjectMapper mapper = new ObjectMapper();
    public static void main(String[] args) {
        SpringApplication.run(SentimentFunction.class, args);
    }

    @Bean
    public Function<byte[], Map<String, Object>> analyzeAndUpload() {
        return input -> {
            List<Map<String, Object>> sentimentResults = new ArrayList<>();
            try {
                String text = new String(input, StandardCharsets.UTF_8);
                String[] critics = text.split("\\r?\\n");

                for (String comment : critics) {
                    if (comment.trim().isEmpty()) continue; // Skip blank lines

                    String sentiment = analyze(comment); // Your existing sentiment logic

                    Map<String, Object> entry = new HashMap<>();
                    entry.put("comment", comment);
                    entry.put("sentiment", sentiment);
                    sentimentResults.add(entry);
                }

                String filename = "sentiment-results-" + System.currentTimeMillis() + ".json";
                String json = mapper.writeValueAsString(sentimentResults);

                return Map.of(
                        "status", "success",
                        "file", filename,
                        "json", json
                );
            } catch (Exception e) {
                return Map.of("error", e.getMessage());
            }
        };
    }

    private String analyze(String text) {
        SentimentPolarities scores = SentimentAnalyzer.getScoresFor(text);
        double compound = scores.getCompoundPolarity();
        if (compound >= 0.5) return "positive";
        else if (compound <= -0.5) return "negative";
        else return "neutral";
    }
}