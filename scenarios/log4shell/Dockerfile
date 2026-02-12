FROM maven:3.8.5-openjdk-8 AS build
ADD . /log4jpwn
WORKDIR /log4jpwn
RUN mvn clean compile assembly:single

FROM ibm-semeru-runtimes:open-8-jdk
COPY --from=build /log4jpwn/target/log4jpwn-1.0-SNAPSHOT-jar-with-dependencies.jar /log4jpwn.jar
ENV JAVA_OPTS="-Dcom.sun.jndi.ldap.object.trustURLCodebase=true"
ENV PWN="CVE-2021-44228"

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /log4jpwn.jar"]
