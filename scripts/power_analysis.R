# ==============================================================================
# A-Priori Power Analysis for 54-Run Fractional Factorial Design
# ==============================================================================
# This script validates whether N=54 is a statistically sufficient sample size 
# for your 2x3x3 experimental design (Algo x Loss x Alpha).

# Install required package if missing
if (!require("pwr")) install.packages("pwr", dependencies=TRUE)
library(pwr)

# ------------------------------------------------------------------------------
# 1. Experimental Design Parameters
# ------------------------------------------------------------------------------
# Factors:
# 1. Algorithm: 2 levels (ZKP, ECC)
# 2. Packet Loss: 3 levels (25%, 50%, 75%)
# 3. Alpha (EWMA): 3 levels (0.1, 0.3, 0.5)
# Total groups (configurations): 2 * 3 * 3 = 18 groups

groups <- 18
target_power <- 0.80 # 80% power is the academic standard
significance_level <- 0.05 # alpha = 0.05

# We expect a LARGE effect size (f = 0.4) because ZKP vs ECC inherently has 
# a massive algorithmic baseline difference (334ms vs 111ms).
effect_size <- 0.40 

cat("=== STATISTICAL POWER ANALYSIS ===\n")
cat("Testing assumption: Is N=54 sufficient for this 18-group design?\n\n")

# ------------------------------------------------------------------------------
# 2. Calculate Required N for 80% Power
# ------------------------------------------------------------------------------
pwr_result <- pwr.anova.test(k = groups, 
                             f = effect_size, 
                             sig.level = significance_level, 
                             power = target_power)

n_per_group <- ceiling(pwr_result$n)
total_n_required <- n_per_group * groups

cat(sprintf("To achieve %.1f%% statistical power (detecting a large effect):\n", target_power*100))
cat(sprintf("- Required replicates per group: %d\n", n_per_group))
cat(sprintf("- Total required runs: %d\n\n", total_n_required))

# ------------------------------------------------------------------------------
# 3. Validate the 54-Run Campaign
# ------------------------------------------------------------------------------
planned_runs <- 54
actual_power <- pwr.anova.test(k = groups, 
                               n = (planned_runs / groups), 
                               f = effect_size, 
                               sig.level = significance_level)$power

cat(sprintf("Your planned 54-run campaign achieves: %.2f%% Statistical Power\n", actual_power*100))

if (actual_power >= 0.80) {
  cat("✅ CONCLUSION: The 54-run fractional factorial design is statistically SUFFICIENT.\n")
} else {
  cat("⚠️ WARNING: The 54-run design is underpowered. Consider increasing iterations (e.g. 5 replicates).\n")
}
