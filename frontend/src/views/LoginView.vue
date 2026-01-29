<script setup lang="ts">
import { SignInButton, SignedOut } from '@clerk/vue'
</script>

<template>
  <div class="login-page">
    <!-- Hero Left -->
    <div class="login-hero">
      <div class="hero-content">
        <span class="material-symbols-rounded hero-shield">shield</span>
        <h1 class="hero-brand">Guard-IA</h1>
        <p class="hero-tagline">AI-Powered Email Threat Intelligence</p>
        <p class="hero-desc">
          Protecting your corporate email with a 3-stage AI pipeline:
          Heuristic Engine, ML Classifier, and LLM Explainer. Real-time detection. Zero trust.
        </p>
        <div class="hero-stats">
          <div class="stat">
            <span class="stat-value">99.57%</span>
            <span class="stat-label">Recall Rate</span>
          </div>
          <div class="stat">
            <span class="stat-value">&lt; 3s</span>
            <span class="stat-label">Avg Response</span>
          </div>
          <div class="stat">
            <span class="stat-value">24/7</span>
            <span class="stat-label">Monitoring</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Sign In Right -->
    <div class="login-form-side">
      <div class="form-container">
        <div class="form-logo">
          <span class="material-symbols-rounded form-shield">shield</span>
          <span class="form-logo-text">Guard-IA</span>
        </div>
        <h2 class="form-heading">Sign in to your account</h2>
        <p class="form-subtitle">Invitation-only access</p>

        <SignedOut>
          <SignInButton mode="modal">
            <button class="sign-in-btn">Sign In with Clerk</button>
          </SignInButton>
        </SignedOut>

        <p class="form-footer">
          Protected by Guard-IA v1.0 | Universidad ORT Uruguay
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Hero Left */
.login-hero {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: #070F1E;
}

.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  max-width: 480px;
}

.hero-shield {
  font-size: 80px;
  color: var(--accent-cyan);
  font-variation-settings: 'wght' 300;
}

.hero-brand {
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -1px;
}

.hero-tagline {
  font-size: 18px;
  color: var(--text-secondary);
  text-align: center;
}

.hero-desc {
  font-size: 14px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.6;
  max-width: 420px;
}

.hero-stats {
  display: flex;
  gap: 40px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-cyan);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* Form Right */
.login-form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 100px;
  background: var(--bg-primary);
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 28px;
  width: 400px;
}

.form-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-shield {
  font-size: 32px;
  color: var(--accent-cyan);
  font-variation-settings: 'wght' 300;
}

.form-logo-text {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.form-heading {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: -16px;
}

.sign-in-btn {
  width: 100%;
  height: 44px;
  background: var(--accent-cyan);
  color: var(--bg-primary);
  border: none;
  border-radius: var(--border-radius-sm);
  font-size: 16px;
  font-weight: 600;
  font-family: var(--font-family);
  cursor: pointer;
  transition: background 0.2s;
}

.sign-in-btn:hover {
  background: var(--accent-cyan-hover);
}

.form-footer {
  font-size: 12px;
  color: var(--text-dim);
  text-align: center;
}

@media (max-width: 1024px) {
  .login-hero {
    display: none;
  }
  .login-form-side {
    padding: 40px 24px;
  }
}
</style>
