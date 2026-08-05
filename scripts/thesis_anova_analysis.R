# ==============================================================================
# Statistical Conclusion & ANOVA Script for DIL Authorization Meshes
# ==============================================================================
# This script parses the 54 ROS 2 CSV files, extracts the physical eviction 
# latency, tests statistical assumptions, and computes the 3-Way ANOVA.

if (!require("dplyr")) install.packages("dplyr", dependencies=TRUE)
if (!require("car")) install.packages("car", dependencies=TRUE)
if (!require("ggplot2")) install.packages("ggplot2", dependencies=TRUE)

library(dplyr)
library(car)
library(ggplot2)

# ------------------------------------------------------------------------------
# 1. Data Ingestion & Feature Extraction
# ------------------------------------------------------------------------------
data_dir <- "data/60_trial_run" # Modify if your data is elsewhere
csv_files <- list.files(path = data_dir, pattern = "*.csv", full.names = TRUE)

if (length(csv_files) == 0) {
  stop(sprintf("No CSV files found in %s! Ensure the 54-run campaign is finished.", data_dir))
}

results_list <- list()

cat("Parsing ROS 2 CSV Telemetry files...\n")
for (file in csv_files) {
  # Extract factors from filename: e.g., trial_ZKP_n2_loss25_iter1.csv
  # Note: Adjust the regex or string splitting based on your exact filename format
  basename <- basename(file)
  parts <- strsplit(basename, "_")[[1]]
  
  if (length(parts) >= 5) {
    algo <- parts[2]
    loss <- as.numeric(gsub("loss", "", parts[4]))
    iter <- as.numeric(gsub(".csv", "", gsub("iter", "", parts[5])))
    
    # Read the CSV
    df <- read.csv(file)
    
    # Compute relative time
    t0 <- df$timestamp_sec[1] + (df$timestamp_nanosec[1] * 1e-9)
    df$time <- (df$timestamp_sec + (df$timestamp_nanosec * 1e-9)) - t0
    
    # Find Attack Trigger
    attack_rows <- subset(df, attack_active == 1)
    if (nrow(attack_rows) > 0) {
      attack_t <- attack_rows$time[1]
      
      # Find Physical Halt (velocity < 0.001 rad/s)
      post_attack <- subset(df, time > attack_t)
      halt_rows <- subset(post_attack, abs(shoulder_pan_vel) < 0.001)
      
      if (nrow(halt_rows) > 0) {
        halt_t <- halt_rows$time[1]
        eviction_latency_ms <- (halt_t - attack_t) * 1000
        
        # We don't have alpha in the filename right now, so we assume it's logged inside or 
        # we can just treat the ANOVA as a 2-way (Algo x Loss) if alpha isn't parsed. 
        # For full 3-way, ensure alpha is extracted.
        
        results_list[[length(results_list) + 1]] <- data.frame(
          Algorithm = algo,
          Loss = as.factor(loss),
          Iteration = iter,
          Latency_ms = eviction_latency_ms
        )
      }
    }
  }
}

final_data <- bind_rows(results_list)
cat(sprintf("Successfully extracted latency for %d trials.\n\n", nrow(final_data)))

if (nrow(final_data) == 0) {
  stop("No valid latency data could be extracted.")
}

# ------------------------------------------------------------------------------
# 2. Assumption Testing
# ------------------------------------------------------------------------------
cat("=== STATISTICAL ASSUMPTIONS ===\n")

# A. Normality Test (Shapiro-Wilk)
# H0: Data is normally distributed
shapiro_test <- shapiro.test(final_data$Latency_ms)
cat(sprintf("Shapiro-Wilk Normality Test (p-value): %.4f\n", shapiro_test$p.value))
if (shapiro_test$p.value < 0.05) {
  cat("⚠️ WARNING: Data significantly deviates from normality (common in hard real-time latency).\n")
} else {
  cat("✅ Data is normally distributed.\n")
}

# B. Homogeneity of Variance (Levene's Test)
# H0: Variances are equal across groups
levene_test <- leveneTest(Latency_ms ~ Algorithm * Loss, data = final_data)
cat(sprintf("Levene's Test for Equal Variance (p-value): %.4f\n", levene_test$`Pr(>F)`[1]))
if (levene_test$`Pr(>F)`[1] < 0.05) {
  cat("⚠️ WARNING: Variances are significantly unequal across groups.\n")
} else {
  cat("✅ Variances are homogeneous.\n")
}
cat("\n")

# ------------------------------------------------------------------------------
# 3. 2-Way (or 3-Way) ANOVA
# ------------------------------------------------------------------------------
cat("=== ANOVA CONCLUSIONS ===\n")
# Assuming we parse Algo and Loss. (If you extract Alpha, add '* Alpha' to the formula)
anova_model <- aov(Latency_ms ~ Algorithm * Loss, data = final_data)
summary_aov <- summary(anova_model)
print(summary_aov)

cat("\n--- ACADEMIC INTERPRETATION ---\n")
# Extract p-values
p_algo <- summary_aov[[1]][["Pr(>F)"]][1]
p_loss <- summary_aov[[1]][["Pr(>F)"]][2]

if (p_algo < 0.05) {
  cat("1. ✅ ALGORITHM EFFECT: There is a statistically significant difference in latency between ZKP and ECC.\n")
} else {
  cat("1. ❌ ALGORITHM EFFECT: No significant difference between ZKP and ECC latency.\n")
}

if (p_loss < 0.05) {
  cat("2. ✅ JAMMING EFFECT: Network packet loss severity significantly impacts eviction latency.\n")
} else {
  cat("2. ❌ JAMMING EFFECT: The mesh is remarkably resilient! Packet loss does NOT significantly affect latency.\n")
}

# ------------------------------------------------------------------------------
# 4. Data Visualization
# ------------------------------------------------------------------------------
cat("\nGenerating Boxplot (saved to Rplots.pdf)...\n")
p <- ggplot(final_data, aes(x=Loss, y=Latency_ms, fill=Algorithm)) +
  geom_boxplot() +
  labs(title="Eviction Latency by Algorithm and Network Packet Loss",
       x="Network Packet Loss (%)",
       y="Physical Halt Latency (ms)") +
  theme_minimal()

print(p)
