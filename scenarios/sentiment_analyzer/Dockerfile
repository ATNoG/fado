# ---- Build stage ----
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt update && \
    apt install -y curl unzip wget zip default-jdk maven

WORKDIR /app
COPY pom.xml .
COPY src ./src

RUN mvn dependency:get -Dartifact=org.springframework.boot.experimental:spring-boot-thin-launcher:1.0.27.RELEASE:jar:exec
RUN mvn clean package

RUN cp target/sentiment_analyzer-2.0.0.RELEASE.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
