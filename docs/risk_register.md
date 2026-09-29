# System Risk Register

## Overview

This Risk Register identifies potential operational, technical, and architectural risks associated with public emergency website capacity planning and simulator execution.

---

## Risk Matrix

| Risk ID | Operational Risk Description | Probability | Impact | Mitigation Strategy | Residual Risk |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **R-01** | **Auto-Scaling Delay Overload**: 180s scaling delay causes queue backlog during rapid 15-minute disaster traffic spikes. | **High** | **High** | Pre-warm extra base instances when advance weather/disaster warnings are issued to eliminate initial scaling delay. | **Low** |
| **R-02** | **Hard Instance Ceiling Exhaustion**: Traffic surge exceeds maximum instance ceiling limit (50 instances = 25,000 RPM). | **Low** | **High** | Increase maximum cloud instance quota ceiling to 80 instances and enable static asset caching via CDN edge networks. | **Low** |
| **R-03** | **Average-Demand Under-Provisioning**: Infrastructure team plans capacity using average demand (~1,300 RPM) instead of disaster peaks. | **High** | **Critical** | Mandate scenario-based capacity testing using this simulator prior to every major disaster season. | **Low** |
| **R-04** | **Corrupted Telemetry Input**: Missing timestamps or negative traffic values cause simulation pipeline or auto-scaler crash. | **Medium** | **Medium** | Automated data cleaning pipeline imputes missing values, clips negative rates, and enforces strict schema validation. | **Low** |
| **R-05** | **Queue Buffer Overflow**: Sustained demand exceeding server processing rate fills queue buffer, causing HTTP 503 drops. | **Medium** | **High** | Implement adaptive queue rate limiting and return lightweight static cached HTML pages during extreme overload. | **Medium** |
| **R-06** | **Misinterpretation of Prototype**: Stakeholders mistake simulation outputs for real-time production monitoring systems. | **Medium** | **Medium** | Prominently display executive disclaimers and role-based access control badges in UI and report outputs. | **Low** |
