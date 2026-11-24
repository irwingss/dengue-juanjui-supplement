# Logistic regression and sensitivity analyses for dengue in Juanjuí.
suppressPackageStartupMessages({ library(sandwich); library(lmtest); library(splines) })
options(width = 200)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript code/31_analysis.R <authorized-data.csv> <output-directory>")
}
TABLES <- args[[2L]]
dir.create(TABLES, recursive = TRUE, showWarnings = FALSE)
B <- read.csv(args[[1L]], encoding = "UTF-8", na.strings = c("", "NA"))
B$included <- B$included %in% c("True", TRUE)
B$sex   <- factor(B$sex, levels = c("M", "F"))
B$month_factor   <- factor(B$month, labels = month.abb[sort(unique(B$month))])
B$group  <- ifelse(B$included, "Included", "Excluded")

# Comparison of included and excluded patients
fmt_n <- function(x, n) sprintf("%d (%.1f)", x, 100 * x / n)
comp <- function(var, levels_to_report, label) {
  do.call(rbind, lapply(levels_to_report, function(k) {
    f <- function(g) { s <- B[B$group == g, ]; fmt_n(sum(s[[var]] == k, na.rm = TRUE), nrow(s)) }
    data.frame(variable = label, category = as.character(k), included = f("Included"), excluded = f("Excluded"))
  }))
}
pval <- function(var) { t <- table(B[[var]], B$group); suppressWarnings(chisq.test(t)$p.value) }
ni <- sum(B$included); ne <- sum(!B$included)
med <- function(g) { x <- B$age[B$group == g]; sprintf("%.0f (%.0f-%.0f)", median(x, na.rm = TRUE), quantile(x, .25, na.rm = TRUE), quantile(x, .75, na.rm = TRUE)) }
B$test_result <- ifelse(B$dengue_positive == 1, "Confirmed", "Test negative")
B$sex_label    <- ifelse(is.na(B$sex), "Not recorded", ifelse(B$sex == "F", "Female", "Male"))
B$occupation_label    <- ifelse(is.na(B$occupation), "Not recorded", B$occupation)
B$sector_label  <- ifelse(is.na(B$sector), "No block recorded", B$sector)
B$month_label     <- as.character(B$month_factor)
T1 <- rbind(
  data.frame(variable = "n", category = "", included = as.character(ni), excluded = as.character(ne)),
  comp("test_result", c("Confirmed", "Test negative"), "Laboratory result"),
  data.frame(variable = "Age, median (IQR)", category = "", included = med("Included"), excluded = med("Excluded")),
  comp("sex_label", c("Female", "Male", "Not recorded"), "Sex"),
  comp("occupation_label", c("Student", "Homemaker", "Other", "Not recorded"), "Occupation"),
  comp("month_label", levels(B$month_factor), "Month of notification"),
  comp("sector_label", sort(unique(B$sector_label)), "Sector"))
p <- c(test_result = pval("test_result"),
       age = wilcox.test(age ~ group, data = B)$p.value,
       sex = pval("sex_label"), occupation = pval("occupation_label"), month = pval("month_label"))
cat("================ Included vs. excluded patients ================\n"); print(T1, row.names = FALSE)
cat("\nP values (chi-square / Wilcoxon):\n"); print(round(p, 4))
write.csv(T1, file.path(TABLES, "included_vs_excluded.csv"), row.names = FALSE)

cat("\nMonthly positivity among notified patients and percentage included:\n")
pm <- aggregate(cbind(notified = 1, positive = dengue_positive, included = included) ~ month_factor, B, sum)
pm$positivity_pct <- round(100 * pm$positive / pm$notified, 1); pm$incl_pct <- round(100 * pm$included / pm$notified, 1)
print(pm)
write.csv(pm, file.path(TABLES, "monthly_positivity.csv"), row.names = FALSE)

# Model for inclusion in the analytical population.
B$incl <- as.integer(B$included)
Bs <- subset(B, !is.na(age))
mi <- glm(incl ~ dengue_positive + age + sex_label + month_factor, data = Bs, family = binomial)
cat("\nInclusion model (odds ratio for inclusion):\n")
print(round(cbind(OR = exp(coef(mi)), exp(confint.default(mi)), p = summary(mi)$coef[, 4]), 3))

# Association models with calendar-time and sector adjustment
A <- subset(B, included)
A$sector <- factor(A$sector)
cat(sprintf("\n================ Individual-level analysis: n = %d (%d confirmed, %d test-negative) ================\n",
            nrow(A), sum(A$dengue_positive), sum(A$dengue_positive == 0)))
cat("Confirmed and test-negative patients included, by month:\n"); print(table(A$month_factor, A$dengue_positive))
cat("Households with Ae. aegypti by month (%):\n"); print(round(100 * tapply(A$household_aedes, A$month_factor, mean), 1))
cat("Sector:\n"); print(table(A$sector, A$dengue_positive, useNA = "ifany"))

odds_ratio <- function(m, term) {
  b <- coef(m)[term]; se <- sqrt(diag(vcov(m)))[term]
  c(OR = exp(b), ci_lower = exp(b - 1.96 * se), ci_upper = exp(b + 1.96 * se), p = 2 * pnorm(-abs(b / se)), n = nobs(m), AIC = AIC(m))
}
# Combine a month with the preceding month if it has fewer than ten included patients.
A$adjusted_month <- A$month_factor
if (min(table(A$month_factor)) < 10) {
  sparse_months <- names(which(table(A$month_factor) < 10)); cat("Months with fewer than 10 patients, grouped with the preceding month:", sparse_months, "\n")
  lv <- levels(A$month_factor); for (k in sparse_months) { j <- match(k, lv); levels(A$adjusted_month)[levels(A$adjusted_month) == k] <- lv[j - 1] }
}
As <- subset(A, !is.na(sex) & !is.na(sector))
cat(sprintf("Complete-case sample for adjusted models: n = %d\n", nrow(As)))
spec <- list(
  "Crude"                                 = dengue_positive ~ household_aedes,
  "Age + sex"                           = dengue_positive ~ household_aedes + age + sex,
  "Age + sex + month"                     = dengue_positive ~ household_aedes + age + sex + adjusted_month,
  "Age + sex + epidemiological week (spline)"     = dengue_positive ~ household_aedes + age + sex + ns(epi_week, 3),
  "Age + sex + month + sector (fixed effects)"     = dengue_positive ~ household_aedes + age + sex + adjusted_month + sector,
  "Age + sex + month + sector + occupation"= dengue_positive ~ household_aedes + age + sex + adjusted_month + sector + occupation)
specIR <- lapply(spec, function(f) update(f, . ~ . - household_aedes + I(container_index * 10)))
fit_models <- function(sp, term, data) do.call(rbind, lapply(names(sp), function(k) {
  d <- if (k == "Crude") data else As
  if (grepl("occupation", k, fixed = TRUE)) d <- subset(As, !is.na(occupation))
  m <- glm(sp[[k]], data = d, family = binomial)
  r <- round(odds_ratio(m, term), 4); names(r) <- c("OR", "ci_lower", "ci_upper", "p", "n", "AIC")
  data.frame(model = k, t(r))
}))
R1 <- fit_models(spec,   "household_aedes", A)
R2 <- fit_models(specIR, "I(container_index * 10)",     A)
cat("\n-- Exposure: household with at least one positive container --\n"); print(R1, row.names = FALSE)
cat("\n-- Exposure: container index, per 10-percentage-point increase --\n"); print(R2, row.names = FALSE)

# Block-clustered standard errors for the main model.
mp <- glm(spec[["Age + sex + month + sector (fixed effects)"]], data = As, family = binomial)
As$cl <- ifelse(As$block > 0, As$block, -As$record_id)
ct <- coeftest(mp, vcovCL(mp, cluster = ~cl))
b <- ct["household_aedes", ]
cat(sprintf("\nMain model with block-clustered standard errors: OR = %.2f (95%% CI %.2f-%.2f), p = %.4f\n",
            exp(b[1]), exp(b[1] - 1.96 * b[2]), exp(b[1] + 1.96 * b[2]), b[4]))
cat("Main model coefficients:\n")
print(round(cbind(OR = exp(coef(mp)), exp(confint.default(mp)), p = summary(mp)$coef[, 4]), 3))

# Sensitivity analysis using inverse probability of inclusion weights
# Weight = 1 / P(included | test result, age, sex, month). The analysis assumes that
# conditional on these variables, exclusion does not depend on household infestation.
B2 <- subset(B, !is.na(age)); B2$pi <- fitted(glm(incl ~ dengue_positive + age + sex_label + month_factor, data = B2, family = binomial))
Aw <- merge(As, B2[, c("record_id", "pi")], by = "record_id"); Aw$w <- 1 / Aw$pi
mw <- suppressWarnings(glm(dengue_positive ~ household_aedes + age + sex + adjusted_month + sector, data = Aw, family = binomial, weights = w))
cw <- coeftest(mw, vcovHC(mw, type = "HC0"))["household_aedes", ]
cat(sprintf("\nIPW (robust standard errors): OR = %.2f (95%% CI %.2f-%.2f), p = %.4f | weight range %.2f-%.2f\n",
            exp(cw[1]), exp(cw[1] - 1.96 * cw[2]), exp(cw[1] + 1.96 * cw[2]), cw[4], min(Aw$w), max(Aw$w)))

R1$exposure <- "Positive household"; R2$exposure <- "Container index (+10 pp)"
write.csv(rbind(R1, R2), file.path(TABLES, "sequential_adjustment_models.csv"), row.names = FALSE)
write.csv(data.frame(analysis = c("Main model with block-clustered standard errors", "Inverse probability of inclusion weighting"),
                     OR = exp(c(b[1], cw[1])), ci_lower = exp(c(b[1] - 1.96 * b[2], cw[1] - 1.96 * cw[2])),
                     ci_upper = exp(c(b[1] + 1.96 * b[2], cw[1] + 1.96 * cw[2])), p = c(b[4], cw[4])),
          file.path(TABLES, "sensitivity_analyses.csv"), row.names = FALSE)
cat("\nTables exported to", TABLES, "\n")

# =====================================================================
# Descriptive statistics, model coefficients and sensitivity analysis omitting sex
# =====================================================================
cat("\n================ Table 2: descriptive statistics by test result ================\n")
A$occupation_label <- ifelse(is.na(A$occupation), "Not recorded", A$occupation)
A$sex_label <- ifelse(is.na(A$sex), "Not recorded", ifelse(A$sex == "F", "Female", "Male"))
A$sector_label <- ifelse(is.na(A$sector), "No sector", as.character(A$sector))
desc_g <- function(g) {
  s <- if (g == "Total") A else A[A$dengue_positive == (g == "Confirmed"), ]
  q <- function(x) sprintf("%.0f (%.0f–%.0f)", median(x), quantile(x, .25), quantile(x, .75))
  cnt <- function(v, k) as.character(sum(s[[v]] == k))
  c(n = nrow(s), age = q(s$age),
    setNames(sapply(c("Female", "Male", "Not recorded"), function(k) cnt("sex_label", k)), paste0("sex_", c("F", "M", "not_recorded"))),
    setNames(sapply(c("Student", "Homemaker", "Other", "Not recorded"), function(k) cnt("occupation_label", k)), paste0("occupation_", 1:4)),
    setNames(sapply(levels(A$month_factor), function(k) cnt("month_label", k)), paste0("month_", levels(A$month_factor))),
    setNames(sapply(c("JUANJUICILLO", "JUANJUI CENTRO", "LA MERCED", "SANTA ROSA", "SAN JUAN", "No sector"), function(k) cnt("sector_label", k)),
             paste0("sector_", 1:6)),
    containers_inspected = sum(s$containers_inspected), containers_inspected_per_household = q(s$containers_inspected), positive_containers = sum(s$positive_containers),
    household_aedes = sprintf("%d (%.1f)", sum(s$household_aedes), 100 * mean(s$household_aedes)),
    container_index = q(100 * s$container_index))
}
confirmed <- desc_g("Confirmed")
T2 <- data.frame(variable = names(confirmed), confirmed = unname(confirmed),
                 test_negative = unname(desc_g("Test negative")), total = unname(desc_g("Total")))
print(T2, row.names = FALSE)
write.csv(T2, file.path(TABLES, "table_2_descriptive_statistics.csv"), row.names = FALSE)

cat("\n================ Table 3: coefficients ================\n")
coefs <- function(m, rob = FALSE) {
  s <- summary(m)$coefficients
  data.frame(term = rownames(s), beta = s[, 1], std_error = s[, 2], z = s[, 3], p = s[, 4],
             OR = exp(s[, 1]), ci_lower = exp(s[, 1] - 1.96 * s[, 2]), ci_upper = exp(s[, 1] + 1.96 * s[, 2]))
}
mA <- glm(dengue_positive ~ household_aedes, data = A, family = binomial)
mB <- glm(dengue_positive ~ household_aedes + age + sex + adjusted_month + sector, data = As, family = binomial)
mC <- glm(dengue_positive ~ I(container_index * 10), data = A, family = binomial)
mD <- glm(dengue_positive ~ I(container_index * 10) + age + sex + adjusted_month + sector, data = As, family = binomial)
T3 <- rbind(cbind(model = "M1 crude", coefs(mA)), cbind(model = "M2 adjusted", coefs(mB)),
            cbind(model = "M3 container index, crude", coefs(mC)), cbind(model = "M4 container index, adjusted", coefs(mD)))
print(T3, digits = 3); write.csv(T3, file.path(TABLES, "table_3_model_coefficients.csv"), row.names = FALSE)
fit <- function(m, d) c(AIC = AIC(m), R2 = mcf(m, glm(dengue_positive ~ 1, data = d, family = binomial)), AUC = auc_(d$dengue_positive, fitted(m)))
mcf <- function(m, m0) as.numeric(1 - logLik(m) / logLik(m0))
auc_ <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }
hl <- function(y, p, g = 10) { q <- cut(p, unique(quantile(p, seq(0, 1, 1 / g))), include.lowest = TRUE)
  ob <- tapply(y, q, sum); ex <- tapply(p, q, sum); nn <- tapply(y, q, length)
  X <- sum((ob - ex)^2 / (ex * (1 - ex / nn)), na.rm = TRUE); pchisq(X, length(levels(q)) - 2, lower.tail = FALSE) }
vif_ <- function(m) { v <- as.matrix(vcov(m))[-1, -1]; max(diag(solve(cov2cor(v)))) }
for (k in list(list("M1", mA, A), list("M2", mB, As), list("M3", mC, A), list("M4", mD, As)))
  cat(sprintf("%s: AIC %.1f  R2McF %.3f  AUC %.3f\n", k[[1]], fit(k[[2]], k[[3]])[1], fit(k[[2]], k[[3]])[2], fit(k[[2]], k[[3]])[3]))
cat(sprintf("M2 Hosmer-Lemeshow p = %.3f | VIF max = %.2f | EPV = %d events / %d parameters\n",
            hl(As$dengue_positive, fitted(mB)), vif_(mB), sum(As$dengue_positive), length(coef(mB)) - 1))
cat("Likelihood-ratio test for month in M2:\n"); print(anova(update(mB, . ~ . - adjusted_month), mB, test = "LRT"))
cat("Likelihood-ratio test for sector in M2:\n"); print(anova(update(mB, . ~ . - sector), mB, test = "LRT"))

cat("\n-- Sensitivity analysis omitting sex --\n")
Ans <- subset(A, !is.na(sector))
mE <- glm(dengue_positive ~ household_aedes + age + adjusted_month + sector, data = Ans, family = binomial)
print(round(odds_ratio(mE, "household_aedes"), 4))
sens <- read.csv(file.path(TABLES, "sensitivity_analyses.csv"))
r <- odds_ratio(mE, "household_aedes")
sens <- rbind(sens, data.frame(analysis = sprintf("Model omitting sex (n = %d)", nrow(Ans)), OR = r[1], ci_lower = r[2], ci_upper = r[3], p = r[4]))
write.csv(sens, file.path(TABLES, "sensitivity_analyses.csv"), row.names = FALSE)
cat("Household infestation among included patients, by test result:\n"); print(table(A$household_aedes, A$dengue_positive))
