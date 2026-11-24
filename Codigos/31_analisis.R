# Reanálisis de dengue e infestación domiciliaria en Juanjuí.
suppressPackageStartupMessages({ library(sandwich); library(lmtest); library(splines) })
options(width = 200)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript Codigos/31_analisis.R <authorized-data.csv> <output-directory>")
}
TABLAS <- args[[2L]]
dir.create(TABLAS, recursive = TRUE, showWarnings = FALSE)
B <- read.csv(args[[1L]], encoding = "UTF-8", na.strings = c("", "NA"))
B$analitica <- B$analitica %in% c("True", TRUE)
B$sexo   <- factor(B$sexo, levels = c("M", "F"))
B$mesf   <- factor(B$mes, labels = month.abb[sort(unique(B$mes))])
B$grupo  <- ifelse(B$analitica, "Incluido", "Excluido")

# ---------------------------------------------------------- Obs 6: incluidos vs excluidos
fmt_n <- function(x, n) sprintf("%d (%.1f)", x, 100 * x / n)
comp <- function(var, niveles, etiq) {
  do.call(rbind, lapply(niveles, function(k) {
    f <- function(g) { s <- B[B$grupo == g, ]; fmt_n(sum(s[[var]] == k, na.rm = TRUE), nrow(s)) }
    data.frame(variable = etiq, categoria = as.character(k), incluidos = f("Incluido"), excluidos = f("Excluido"))
  }))
}
pval <- function(var) { t <- table(B[[var]], B$grupo); suppressWarnings(chisq.test(t)$p.value) }
ni <- sum(B$analitica); ne <- sum(!B$analitica)
med <- function(g) { x <- B$edad[B$grupo == g]; sprintf("%.0f (%.0f-%.0f)", median(x, na.rm = TRUE), quantile(x, .25, na.rm = TRUE), quantile(x, .75, na.rm = TRUE)) }
B$resultado <- ifelse(B$denguepositivo == 1, "Confirmado", "Descartado")
B$sexo_t    <- ifelse(is.na(B$sexo), "No registrado", ifelse(B$sexo == "F", "Femenino", "Masculino"))
B$ocup_t    <- ifelse(is.na(B$ocupacion), "No registrada", B$ocupacion)
B$sector_t  <- ifelse(is.na(B$sector), "Sin manzana registrada", B$sector)
B$mes_t     <- as.character(B$mesf)
T1 <- rbind(
  data.frame(variable = "n", categoria = "", incluidos = as.character(ni), excluidos = as.character(ne)),
  comp("resultado", c("Confirmado", "Descartado"), "Resultado de laboratorio"),
  data.frame(variable = "Edad, mediana (RIC)", categoria = "", incluidos = med("Incluido"), excluidos = med("Excluido")),
  comp("sexo_t", c("Femenino", "Masculino", "No registrado"), "Sexo"),
  comp("ocup_t", c("Estudiante", "Ama de casa", "Otra", "No registrada"), "Ocupacion"),
  comp("mes_t", levels(B$mesf), "Mes de notificacion"),
  comp("sector_t", sort(unique(B$sector_t)), "Sector"))
p <- c(resultado = pval("resultado"),
       edad = wilcox.test(edad ~ grupo, data = B)$p.value,
       sexo = pval("sexo_t"), ocupacion = pval("ocup_t"), mes = pval("mes_t"))
cat("================ Obs 6: incluidos vs excluidos ================\n"); print(T1, row.names = FALSE)
cat("\nValores p (chi2 / Wilcoxon):\n"); print(round(p, 4))
write.csv(T1, file.path(TABLAS, "T_incluidos_vs_excluidos.csv"), row.names = FALSE)

cat("\nPositividad por mes (todos los notificados) y proporcion incluida:\n")
pm <- aggregate(cbind(notificados = 1, positivos = denguepositivo, incluidos = analitica) ~ mesf, B, sum)
pm$positividad <- round(100 * pm$positivos / pm$notificados, 1); pm$incl_pct <- round(100 * pm$incluidos / pm$notificados, 1)
print(pm)
write.csv(pm, file.path(TABLAS, "T_positividad_por_mes.csv"), row.names = FALSE)

# Modelo de inclusion (determinantes de que la vivienda se inspeccionara)
B$incl <- as.integer(B$analitica)
Bs <- subset(B, !is.na(edad))
mi <- glm(incl ~ denguepositivo + edad + sexo_t + mesf, data = Bs, family = binomial)
cat("\nModelo de inclusion (OR de ser incluido):\n")
print(round(cbind(OR = exp(coef(mi)), exp(confint.default(mi)), p = summary(mi)$coef[, 4]), 3))

# ---------------------------------------------------------- Obs 7: tiempo calendario y sector
A <- subset(B, analitica)
A$sector <- factor(A$sector)
cat(sprintf("\n================ Analisis individual: n = %d (%d confirmados, %d descartados) ================\n",
            nrow(A), sum(A$denguepositivo), sum(A$denguepositivo == 0)))
cat("Confirmados / notificados incluidos por mes:\n"); print(table(A$mesf, A$denguepositivo))
cat("Vivienda con Ae. aegypti por mes (%):\n"); print(round(100 * tapply(A$aedes_vivienda, A$mesf, mean), 1))
cat("Sector:\n"); print(table(A$sector, A$denguepositivo, useNA = "ifany"))

or_de <- function(m, term) {
  b <- coef(m)[term]; se <- sqrt(diag(vcov(m)))[term]
  c(OR = exp(b), inf = exp(b - 1.96 * se), sup = exp(b + 1.96 * se), p = 2 * pnorm(-abs(b / se)), n = nobs(m), AIC = AIC(m))
}
# meses con pocos casos: junio se une a mayo si es necesario
A$mes2 <- A$mesf
if (min(table(A$mesf)) < 10) {
  peq <- names(which(table(A$mesf) < 10)); cat("Meses con < 10 casos agrupados con el mes previo:", peq, "\n")
  lv <- levels(A$mesf); for (k in peq) { j <- match(k, lv); levels(A$mes2)[levels(A$mes2) == k] <- lv[j - 1] }
}
As <- subset(A, !is.na(sexo) & !is.na(sector))
cat(sprintf("Muestra completa para modelos ajustados: n = %d\n", nrow(As)))
spec <- list(
  "Crudo"                                 = denguepositivo ~ aedes_vivienda,
  "Edad + sexo"                           = denguepositivo ~ aedes_vivienda + edad + sexo,
  "Edad + sexo + mes"                     = denguepositivo ~ aedes_vivienda + edad + sexo + mes2,
  "Edad + sexo + semana epi (spline)"     = denguepositivo ~ aedes_vivienda + edad + sexo + ns(semana_epi, 3),
  "Edad + sexo + mes + sector (fijo)"     = denguepositivo ~ aedes_vivienda + edad + sexo + mes2 + sector,
  "Edad + sexo + mes + sector + ocupacion"= denguepositivo ~ aedes_vivienda + edad + sexo + mes2 + sector + ocupacion)
specIR <- lapply(spec, function(f) update(f, . ~ . - aedes_vivienda + I(ir * 10)))
ajusta <- function(sp, term, datos) do.call(rbind, lapply(names(sp), function(k) {
  d <- if (k == "Crudo") datos else As
  if (grepl("ocupacion", k)) d <- subset(As, !is.na(ocupacion))
  m <- glm(sp[[k]], data = d, family = binomial)
  r <- round(or_de(m, term), 4); names(r) <- c("OR", "inf", "sup", "p", "n", "AIC")
  data.frame(modelo = k, t(r))
}))
R1 <- ajusta(spec,   "aedes_vivienda", A)
R2 <- ajusta(specIR, "I(ir * 10)",     A)
cat("\n-- Exposicion: vivienda con al menos un recipiente positivo --\n"); print(R1, row.names = FALSE)
cat("\n-- Exposicion: indice de recipientes, por cada 10 puntos porcentuales --\n"); print(R2, row.names = FALSE)

# errores robustos por manzana (conglomerado) en el modelo principal
mp <- glm(spec[["Edad + sexo + mes + sector (fijo)"]], data = As, family = binomial)
As$cl <- ifelse(As$mz > 0, As$mz, -As$n)
ct <- coeftest(mp, vcovCL(mp, cluster = ~cl))
b <- ct["aedes_vivienda", ]
cat(sprintf("\nModelo principal con EE robustos por manzana: OR = %.2f (IC95%% %.2f-%.2f), p = %.4f\n",
            exp(b[1]), exp(b[1] - 1.96 * b[2]), exp(b[1] + 1.96 * b[2]), b[4]))
cat("Coeficientes completos del modelo principal:\n")
print(round(cbind(OR = exp(coef(mp)), exp(confint.default(mp)), p = summary(mp)$coef[, 4]), 3))

# ---------------------------------------------------------- Sensibilidad: IPW por inclusion
# Peso = 1 / P(incluido | resultado, edad, sexo, mes): corrige que los descartados se
# perdieran con mas frecuencia, bajo el supuesto de que la perdida no depende de la
# infestacion una vez condicionada a esas variables (no verificable: ver Limitaciones).
B2 <- subset(B, !is.na(edad)); B2$pi <- fitted(glm(incl ~ denguepositivo + edad + sexo_t + mesf, data = B2, family = binomial))
Aw <- merge(As, B2[, c("n", "pi")], by = "n"); Aw$w <- 1 / Aw$pi
mw <- suppressWarnings(glm(denguepositivo ~ aedes_vivienda + edad + sexo + mes2 + sector, data = Aw, family = binomial, weights = w))
cw <- coeftest(mw, vcovHC(mw, type = "HC0"))["aedes_vivienda", ]
cat(sprintf("\nIPW (EE robustos): OR = %.2f (IC95%% %.2f-%.2f), p = %.4f | peso rango %.2f-%.2f\n",
            exp(cw[1]), exp(cw[1] - 1.96 * cw[2]), exp(cw[1] + 1.96 * cw[2]), cw[4], min(Aw$w), max(Aw$w)))

R1$exposicion <- "Vivienda positiva"; R2$exposicion <- "IR (+10 pp)"
write.csv(rbind(R1, R2), file.path(TABLAS, "T_modelos_ajuste_secuencial.csv"), row.names = FALSE)
write.csv(data.frame(analisis = c("Principal EE robustos manzana", "IPW inclusion"),
                     OR = exp(c(b[1], cw[1])), inf = exp(c(b[1] - 1.96 * b[2], cw[1] - 1.96 * cw[2])),
                     sup = exp(c(b[1] + 1.96 * b[2], cw[1] + 1.96 * cw[2])), p = c(b[4], cw[4])),
          file.path(TABLAS, "T_sensibilidad.csv"), row.names = FALSE)
cat("\nTablas exportadas a", TABLAS, "\n")

# =====================================================================
# Tablas del manuscrito (Tabla 2, Tabla 3) y sensibilidad sin la variable sexo
# =====================================================================
cat("\n================ Tabla 2: descriptivos por resultado ================\n")
A$ocup_t <- ifelse(is.na(A$ocupacion), "No registrada", A$ocupacion)
A$sexo_t <- ifelse(is.na(A$sexo), "No registrado", ifelse(A$sexo == "F", "Femenino", "Masculino"))
A$sector_t <- ifelse(is.na(A$sector), "Sin sector", as.character(A$sector))
desc_g <- function(g) {
  s <- if (g == "Total") A else A[A$denguepositivo == (g == "Confirmado"), ]
  q <- function(x) sprintf("%.0f (%.0f–%.0f)", median(x), quantile(x, .25), quantile(x, .75))
  cnt <- function(v, k) as.character(sum(s[[v]] == k))
  c(n = nrow(s), edad = q(s$edad),
    setNames(sapply(c("Femenino", "Masculino", "No registrado"), function(k) cnt("sexo_t", k)), paste0("sexo_", c("F", "M", "NR"))),
    setNames(sapply(c("Estudiante", "Ama de casa", "Otra", "No registrada"), function(k) cnt("ocup_t", k)), paste0("ocup_", 1:4)),
    setNames(sapply(levels(A$mesf), function(k) cnt("mes_t", k)), paste0("mes_", levels(A$mesf))),
    setNames(sapply(c("JUANJUICILLO", "JUANJUI CENTRO", "LA MERCED", "SANTA ROSA", "SAN JUAN", "Sin sector"), function(k) cnt("sector_t", k)),
             paste0("sec_", 1:6)),
    rec_insp = sum(s$recinsp), rec_insp_viv = q(s$recinsp), rec_pos = sum(s$recpos),
    viv_aedes = sprintf("%d (%.1f)", sum(s$aedes_vivienda), 100 * mean(s$aedes_vivienda)),
    ir = q(100 * s$ir))
}
T2 <- data.frame(Confirmado = desc_g("Confirmado"), Descartado = desc_g("Descartado"), Total = desc_g("Total"))
print(T2); write.csv(T2, file.path(TABLAS, "T2_descriptivos.csv"))

cat("\n================ Tabla 3: coeficientes ================\n")
coefs <- function(m, rob = FALSE) {
  s <- summary(m)$coefficients
  data.frame(termino = rownames(s), beta = s[, 1], ee = s[, 2], z = s[, 3], p = s[, 4],
             OR = exp(s[, 1]), inf = exp(s[, 1] - 1.96 * s[, 2]), sup = exp(s[, 1] + 1.96 * s[, 2]))
}
mA <- glm(denguepositivo ~ aedes_vivienda, data = A, family = binomial)
mB <- glm(denguepositivo ~ aedes_vivienda + edad + sexo + mes2 + sector, data = As, family = binomial)
mC <- glm(denguepositivo ~ I(ir * 10), data = A, family = binomial)
mD <- glm(denguepositivo ~ I(ir * 10) + edad + sexo + mes2 + sector, data = As, family = binomial)
T3 <- rbind(cbind(modelo = "M1 crudo", coefs(mA)), cbind(modelo = "M2 ajustado", coefs(mB)),
            cbind(modelo = "M3 IR crudo", coefs(mC)), cbind(modelo = "M4 IR ajustado", coefs(mD)))
print(T3, digits = 3); write.csv(T3, file.path(TABLAS, "T3_modelos.csv"), row.names = FALSE)
fit <- function(m, d) c(AIC = AIC(m), R2 = mcf(m, glm(denguepositivo ~ 1, data = d, family = binomial)), AUC = auc_(d$denguepositivo, fitted(m)))
mcf <- function(m, m0) as.numeric(1 - logLik(m) / logLik(m0))
auc_ <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }
hl <- function(y, p, g = 10) { q <- cut(p, unique(quantile(p, seq(0, 1, 1 / g))), include.lowest = TRUE)
  ob <- tapply(y, q, sum); ex <- tapply(p, q, sum); nn <- tapply(y, q, length)
  X <- sum((ob - ex)^2 / (ex * (1 - ex / nn)), na.rm = TRUE); pchisq(X, length(levels(q)) - 2, lower.tail = FALSE) }
vif_ <- function(m) { v <- as.matrix(vcov(m))[-1, -1]; max(diag(solve(cov2cor(v)))) }
for (k in list(list("M1", mA, A), list("M2", mB, As), list("M3", mC, A), list("M4", mD, As)))
  cat(sprintf("%s: AIC %.1f  R2McF %.3f  AUC %.3f\n", k[[1]], fit(k[[2]], k[[3]])[1], fit(k[[2]], k[[3]])[2], fit(k[[2]], k[[3]])[3]))
cat(sprintf("M2 Hosmer-Lemeshow p = %.3f | VIF max = %.2f | EPV = %d eventos / %d parametros\n",
            hl(As$denguepositivo, fitted(mB)), vif_(mB), sum(As$denguepositivo), length(coef(mB)) - 1))
cat("LRT del mes en M2:\n"); print(anova(update(mB, . ~ . - mes2), mB, test = "LRT"))
cat("LRT del sector en M2:\n"); print(anova(update(mB, . ~ . - sector), mB, test = "LRT"))

cat("\n-- Sensibilidad sin la variable sexo (el sexo falta casi solo en confirmados) --\n")
Ans <- subset(A, !is.na(sector))
mE <- glm(denguepositivo ~ aedes_vivienda + edad + mes2 + sector, data = Ans, family = binomial)
print(round(or_de(mE, "aedes_vivienda"), 4))
sens <- read.csv(file.path(TABLAS, "T_sensibilidad.csv"))
r <- or_de(mE, "aedes_vivienda")
sens <- rbind(sens, data.frame(analisis = sprintf("Sin la variable sexo (n = %d)", nrow(Ans)), OR = r[1], inf = r[2], sup = r[3], p = r[4]))
write.csv(sens, file.path(TABLAS, "T_sensibilidad.csv"), row.names = FALSE)
cat("Infestacion de la vivienda en incluidos por resultado:\n"); print(table(A$aedes_vivienda, A$denguepositivo))
