VALUATION RESULTS
============================================================

Metric                              Value
------------------------------------------
Accuracy                           0.7912
Precision (macro)                  0.8796
Precision (weighted)               0.9615
Recall (macro)                     0.7984
Recall (weighted)                  0.7912
F1 (macro)                         0.7327
F1 (weighted)                      0.8266
ROC-AUC (macro OvR)                0.9478
Top-2 Accuracy                     0.8560

Per-class F1 scores:
------------------------------------------
  deadline                  1.0000  ████████████████████
  interview_call            1.0000  ████████████████████
  news                      0.9614  ███████████████████
  confirmation_email        0.1385  ██
  otp                       0.9914  ███████████████████
  expired_email             0.2941  █████
  other                     0.7435  ██████████████

Detailed Classification Report:
------------------------------------------------------------
                    precision    recall  f1-score   support

          deadline     1.0000    1.0000    1.0000       117
    interview_call     1.0000    1.0000    1.0000       115
              news     0.9987    0.9268    0.9614       806
confirmation_email     1.0000    0.0744    0.1385       121
               otp     0.9877    0.9951    0.9914       405
     expired_email     0.1724    1.0000    0.2941       110
             other     0.9981    0.5923    0.7435       888

          accuracy                         0.7912      2562
         macro avg     0.8796    0.7984    0.7327      2562
      weighted avg     0.9615    0.7912    0.8266      2562


Confusion matrix saved to: evaluation/plots/confusion_matrix.png
Per-class metrics chart saved to: evaluation/plots/per_class_metrics.png
Metrics CSV saved to: evaluation/plots/metrics.csv

✅ Evaluation complete.