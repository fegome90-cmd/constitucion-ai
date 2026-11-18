# Java · Maven + JUnit 6 + Spotless

Requiere Java >=21 y Maven >=3.9, ambos disponibles en PATH. No se entrega wrapper binario sin descargarlo de fuente verificada.

```sh
mvn -q -DskipTests package
mvn spotless:apply
mvn spotless:check
mvn test
mvn package
java -cp target/classes org.example.starter.App
```

`mvn -N wrapper:wrapper` permite agregar el Maven Wrapper en un entorno conectado. Maven no usa un lockfile transitivo estándar; mantener las versiones explícitas y verificar resolución antes de publicar.

Control integrado (`check`): `mvn spotless:check verify`.
