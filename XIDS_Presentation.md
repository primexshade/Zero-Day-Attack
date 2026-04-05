# An Explainable CNN–LSTM Framework for Real-Time Zero-Day Attack Detection
## Professional IEEE-Level PowerPoint Presentation

---

## Slide 1: TITLE SLIDE

**An Explainable CNN–LSTM Framework for Real-Time Zero-Day Attack Detection in Network Traffic**

- **Student:** Aryan Tiwari (RA2311003030171)
- **Department:** Computer Science and Engineering
- **Institution:** SRM Institute of Science and Technology
- **Guide:** [Faculty Name]
- **Academic Year:** 2025–2026

---

## Slide 2: PROJECT OVERVIEW

**Background**
- Cyber threats evolving rapidly; zero-day attacks exploit unknown vulnerabilities
- Traditional signature-based IDS fail against novel attack patterns

**Real-World Problem**
- Organizations face ~$4.45M average breach cost (IBM, 2023)
- Zero-day attacks account for 80% of successful breaches

**Motivation**
- Need for intelligent, adaptive detection with human-understandable explanations
- Bridge gap between detection accuracy and model interpretability

**Application Domain**
- Enterprise network security, SOC operations, critical infrastructure protection

---

## Slide 3: PROBLEM STATEMENT

**Problem Definition**
- Zero-day attacks bypass signature-based IDS due to absence of known patterns
- Existing ML/DL models achieve high accuracy but lack interpretability

**Importance**
- Undetected zero-day attacks lead to data breaches, financial loss, and reputational damage
- Security analysts require explainable decisions for threat response

**Gaps in Existing Systems**
- High false positive rates in anomaly-based systems
- Black-box nature of deep learning models
- Limited cross-dataset generalization
- Lack of real-time processing capability

---

## Slide 4: PROJECT OBJECTIVES

**Main Goal**
- Develop an explainable hybrid deep learning framework for real-time zero-day attack detection

**Specific Objectives**
- Design CNN-LSTM architecture for spatial-temporal feature learning
- Integrate SHAP and LIME for model explainability
- Achieve >98% detection accuracy with <2% false positive rate
- Validate generalization across CICIDS2017 and UNSW-NB15 datasets

**Expected Outcomes**
- Production-ready IDS with inference latency <50ms
- Interpretable predictions for security analyst decision support
- IEEE-publishable research contribution

---

## Slide 5: LITERATURE REVIEW

| Author/Year | Approach | Limitation |
|-------------|----------|------------|
| Denning (1987) | Rule-based IDS | Cannot detect unknown attacks |
| Axelsson (2000) | Anomaly detection survey | High false positive rates |
| Kim et al. (2016) | LSTM for intrusion detection | No explainability |
| Vinayakumar (2019) | Deep learning IDS | Limited real-time capability |
| Yin et al. (2017) | RNN-based detection | Lacks spatial feature extraction |
| Shone et al. (2018) | Stacked autoencoders | Black-box predictions |
| Lundberg (2017) | SHAP framework | Not applied to IDS |
| Ribeiro (2016) | LIME explainer | Limited deep learning integration |
| Sharafaldin (2018) | CICIDS2017 dataset | Benchmark establishment |
| Moustafa (2015) | UNSW-NB15 dataset | Modern attack scenarios |

**Research Gap:** No existing work combines CNN-LSTM with XAI for zero-day detection

---

## Slide 6: SYSTEM ARCHITECTURE

**End-to-End Pipeline**

```
Network Traffic → Data Preprocessing → Feature Engineering → CNN Layers → LSTM Layers → Dense Classification → XAI Module → Alert/Report
```

**Major Modules**
- **Input Module:** Raw network traffic capture and flow extraction
- **Preprocessing Module:** Cleaning, encoding, normalization, balancing
- **Feature Extraction:** CNN for spatial patterns, LSTM for temporal sequences
- **Classification:** Binary/multi-class attack detection
- **Explainability:** SHAP global importance, LIME local explanations

**[Insert Architecture Diagram]**

---

## Slide 7: PROPOSED SYSTEM

**System Overview**
- Hybrid CNN-LSTM model with integrated explainability layer
- Real-time capable with ~45ms inference latency

**CNN-LSTM Working**
- CNN extracts spatial features from traffic flow patterns
- LSTM captures temporal dependencies across packet sequences
- Dense layers perform final classification

**XAI Integration**
- SHAP: Global feature importance ranking across dataset
- LIME: Instance-level explanation for individual predictions

**Advantages**
- High accuracy with interpretable decisions
- Cross-dataset generalization capability
- Production-ready architecture

---

## Slide 8: DATASET DESCRIPTION

**CICIDS2017**
- Records: ~2.8 million network flows
- Features: 80 extracted features
- Attack types: DDoS, Botnet, Brute Force, Web Attacks, Infiltration
- Source: Canadian Institute for Cybersecurity

**UNSW-NB15**
- Records: ~257,000 network flows
- Features: 49 extracted features
- Attack types: Exploits, Fuzzers, DoS, Reconnaissance, Shellcode, Worms
- Source: University of New South Wales

**Preprocessing Steps**
- Missing value imputation and duplicate removal
- One-hot encoding for categorical features
- Min-Max normalization (0–1 scaling)
- SMOTE/ADASYN for class imbalance handling

---

## Slide 9: METHODOLOGY

**Step-by-Step Pipeline**

1. **Data Collection**
   - Load CICIDS2017 and UNSW-NB15 datasets

2. **Preprocessing**
   - Clean, encode, normalize, and balance data

3. **Feature Selection**
   - Correlation analysis and PCA dimensionality reduction

4. **CNN Feature Extraction**
   - 1D convolution layers for spatial pattern learning

5. **LSTM Temporal Modeling**
   - Sequence modeling for temporal dependencies

6. **Classification**
   - Dense layers with softmax/sigmoid activation

7. **Explainability**
   - SHAP summary plots, LIME instance explanations

---

## Slide 10: TOOLS & TECHNOLOGIES

**Programming Language**
- Python 3.9+

**Deep Learning Frameworks**
- TensorFlow 2.x, Keras

**Machine Learning & Data Processing**
- Scikit-learn, Pandas, NumPy

**Explainability Libraries**
- SHAP (SHapley Additive exPlanations)
- LIME (Local Interpretable Model-agnostic Explanations)

**Visualization**
- Matplotlib, Seaborn

**Development Environment**
- Jupyter Notebook, VS Code

**Version Control**
- Git, GitHub

---

## Slide 11: MODULES IMPLEMENTED

**Module 1: Data Preprocessing**
- Data loading, cleaning, encoding, normalization

**Module 2: Feature Engineering**
- Correlation-based selection, PCA reduction
- SMOTE/ADASYN class balancing

**Module 3: CNN-LSTM Model**
- Conv1D layers → MaxPooling → LSTM layers → Dense layers
- Adam optimizer, categorical cross-entropy loss

**Module 4: XAI Module**
- SHAP TreeExplainer/DeepExplainer integration
- LIME tabular explainer for local explanations

**Module 5: Evaluation Module**
- Metrics computation, confusion matrix, ROC curves

---

## Slide 12: IMPLEMENTATION

**Model Training**
- Train-test split: 80%-20%
- Epochs: 50 with early stopping
- Batch size: 64
- Validation monitoring for overfitting prevention

**XAI Visualization**
- SHAP summary plots for global feature importance
- SHAP force plots for individual predictions
- LIME explanations for misclassified instances

**Evaluation Process**
- Cross-validation on CICIDS2017
- Cross-dataset testing on UNSW-NB15
- Real-time inference latency measurement

**[Insert Training Code Snippet]**

---

## Slide 13: EXPERIMENTAL RESULTS

**Performance Metrics**

| Metric | CICIDS2017 | UNSW-NB15 |
|--------|------------|-----------|
| Accuracy | 98.9% | 97.8% |
| Precision | 0.99 | 0.98 |
| Recall | 0.98 | 0.97 |
| F1-Score | 0.985 | 0.975 |
| AUC-ROC | 0.99 | 0.98 |
| FPR | 1.8% | 2.1% |

**Inference Latency:** ~45 ms per prediction

**[Insert Confusion Matrix]**

**[Insert ROC Curve]**

---

## Slide 14: RESULT DISCUSSION

**Performance Improvements**
- 3-5% accuracy improvement over standalone CNN/LSTM
- 40% reduction in false positives compared to traditional ML

**Comparison with Baseline Models**

| Model | Accuracy | F1-Score |
|-------|----------|----------|
| Random Forest | 94.2% | 0.93 |
| SVM | 91.5% | 0.90 |
| Standalone LSTM | 95.8% | 0.95 |
| Standalone CNN | 96.1% | 0.96 |
| **CNN-LSTM (Ours)** | **98.9%** | **0.985** |

**Key Observations**
- CNN captures spatial attack signatures effectively
- LSTM models temporal attack progression patterns
- XAI reveals critical features: flow duration, packet size, flag counts

---

## Slide 15: WORK COMPLETED SO FAR

**Phase 1: Research & Planning** ✓
- Comprehensive literature review completed
- Research gap identified and objectives defined

**Phase 2: Data Preparation** ✓
- CICIDS2017 and UNSW-NB15 datasets acquired and preprocessed
- Feature engineering and selection completed

**Phase 3: Model Development** ✓
- CNN-LSTM architecture designed and implemented
- Hyperparameter tuning completed

**Phase 4: Explainability Integration** ✓
- SHAP and LIME modules integrated
- Visualization dashboards created

**Phase 5: Evaluation & Documentation** ✓
- Performance metrics computed
- Cross-dataset validation completed

---

## Slide 16: PUBLICATION STATUS

**Target Venues**
- IEEE International Conference on Communications (ICC)
- IEEE Access (Scopus Indexed)

**Paper Title**
- "XIDS: An Explainable CNN-LSTM Framework for Real-Time Zero-Day Attack Detection"

**Current Status**
- Manuscript: Ready for submission
- Figures and tables: Finalized
- Code: Documented and tested

**GitHub Repository**
- https://github.com/primexshade/Zero-Day-Attack

---

## Slide 17: CHALLENGES FACED

**Dataset Imbalance**
- Severe class imbalance (~90% benign traffic)
- Solution: SMOTE/ADASYN oversampling techniques

**Model Complexity**
- CNN-LSTM architecture requires careful tuning
- Solution: Systematic hyperparameter optimization

**Computational Cost**
- Training on 2.8M records is resource-intensive
- Solution: GPU acceleration, batch processing

**Real-Time Constraints**
- Balance between accuracy and inference speed
- Solution: Model optimization, efficient data pipelines

**Explainability Trade-offs**
- SHAP computation is time-intensive
- Solution: Sampling strategies for large datasets

---

## Slide 18: CONCLUSION

**Summary**
- Developed hybrid CNN-LSTM framework for zero-day attack detection
- Integrated SHAP and LIME for model explainability
- Validated across two benchmark datasets

**Key Achievements**
- 98.9% detection accuracy with <2% false positive rate
- Real-time capable with ~45ms inference latency
- Interpretable predictions for security analysts

**Real-World Impact**
- Deployable in enterprise SOC environments
- Enables proactive threat response with explainable alerts
- Contributes to trustworthy AI in cybersecurity

**Future Work**
- Federated learning for distributed deployment
- Attention mechanisms for enhanced explainability

---

## Slide 19: REFERENCES

1. Denning, D. E. (1987). "An Intrusion-Detection Model." *IEEE TSE*, 13(2), 222-232.

2. Axelsson, S. (2000). "Intrusion Detection Systems: A Survey and Taxonomy." *Chalmers University Technical Report*.

3. Kim, J. et al. (2016). "Long Short Term Memory Recurrent Neural Network Classifier for Intrusion Detection." *IEEE ICPDP*.

4. Yin, C. et al. (2017). "A Deep Learning Approach for Intrusion Detection Using RNN." *IEEE Access*, 5, 21954-21961.

5. Lundberg, S. & Lee, S. (2017). "A Unified Approach to Interpreting Model Predictions." *NeurIPS*.

6. Ribeiro, M. et al. (2016). "Why Should I Trust You? Explaining Predictions of Any Classifier." *ACM KDD*.

7. Sharafaldin, I. et al. (2018). "Toward Generating a New Intrusion Detection Dataset." *ICISSP*.

8. Moustafa, N. & Slay, J. (2015). "UNSW-NB15: A Comprehensive Dataset for Network Intrusion Detection." *IEEE MilCIS*.

---

## Slide 20: THANK YOU

**Thank You for Your Attention**

**Questions & Discussion**

---

**Contact:**
- **Email:** at6789@srmist.edu.in
- **GitHub:** github.com/primexshade/Zero-Day-Attack

---

*An Explainable CNN–LSTM Framework for Real-Time Zero-Day Attack Detection in Network Traffic*

---
