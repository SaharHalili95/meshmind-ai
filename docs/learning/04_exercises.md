# 5️⃣ תרגילים מעשיים

> הדרך הטובה ביותר להבין קוד היא לשנות אותו. התרגילים מדורגים מקל לקשה.
> אחרי כל תרגיל: `make test && make lint`.

[⬅ חזרה לאזור הלמידה](README.md)

---

## 🟢 רמה 1: שינוי פרמטרים (בלי לשנות קוד)

צרו קובץ `configs/my_experiment.yaml` (העתק של `default.yaml`) והריצו:

```bash
python -m meshmind.cli experiments --config configs/my_experiment.yaml --results-dir results/my_run
```

| # | שנו | שאלה לחשוב עליה |
|---|---|---|
| 1.1 | `profile: moderate` | למה כל המדיניות כמעט שוות? ([תקלה #17](03_troubleshooting.md#17-כל-המדיניות-חוץ-מ-random-נותנות-כמעט-אותה-תוצאה)) |
| 1.2 | `epsilon_decay: 0.99` | ε מגיע לרצפה אחרי ~300 פרקים. האם הסוכן מספיק לחקור? |
| 1.3 | `gamma: 0.5` | מה קורה לחשיבות של בונוס המסירה (+10) שנמצא 4-5 צעדים קדימה? |
| 1.4 | `loop_penalty: -50.0` | האם reward hacking חוזר? בדקו את עמודת `routing_failures`. |
| 1.5 | `capacity_scale: 0.7` | רשת צפופה יותר: האם הפער בין Q-learning ל-shortest path גדל? |

---

## 🟡 רמה 2: הרחבות קטנות

### 2.1 טופולוגיה חדשה
הוסיפו ל-`topology.py` טופולוגיה בשם `ring_8` (טבעת של 8 צמתים עם 2 קיצורי דרך).

<details>
<summary>💡 רמז</summary>

הגדירו `RING_8_LINKS` כ-tuple של `LinkSpec`, הוסיפו ענף ל-`from_name()` ועדכנו את
`TOPOLOGY_NAMES`. אל תשכחו בדיקה ב-`test_topology.py` שמוודאת 8 צמתים וגרף strongly connected.
</details>

### 2.2 מדד חדש: אחוז מסלולים אופטימליים
הוסיפו ל-`MetricsTracker` מדד: איזה אחוז מהזרימות שנמסרו עברו בנתיב בעל ה-base latency
הנמוך ביותר.

<details>
<summary>💡 רמז</summary>

`FlowResult.path` כבר שומר את המסלול. השוו אותו ל-`shortest_path(topology, src, dst)`.
שימו לב: המדד צריך גישה לטופולוגיה, אז עדיף לחשב אותו ב-`evaluation.py` ולא ב-`metrics.py`
(למה? רמז: גרף התלויות ב-[ארכיטקטורה 2.3](02_architecture.md#23-רמה-3-גרף-תלויות-מדויק-בין-מודולים)).
</details>

### 2.3 גרף חדש: התפלגות כשלים
הוסיפו ל-`plotting.py` גרף עמודות מוערמות של `failure_breakdown()` לכל מדיניות.

---

## 🟠 רמה 3: שיפורי אלגוריתם

### 3.1 Double Q-learning
החליפו את ה-update בגרסה עם שתי טבלאות, כדי להפחית overestimation bias:

```
בהסתברות 0.5:
    a* = argmax_a' Q_A(s', a')
    Q_A(s,a) ← Q_A(s,a) + α [ r + γ · Q_B(s', a*) − Q_A(s,a) ]
אחרת: אותו דבר עם A ו-B מוחלפים
בחירת פעולה: לפי Q_A + Q_B
```

**בדיקה נדרשת:** חשבו ידנית update אחד ובדקו אותו, כמו `test_exact_bellman_update`.

### 3.2 State עשיר יותר: ניצולת הקישור המועמד
במקום ממוצע הניצולת היוצאת, הוסיפו ל-state את ה-bin של **כל** קישור יוצא
(tuple של bins).

<details>
<summary>💡 שאלות לחשוב עליהן</summary>

* פי כמה גדל מרחב המצבים בצומת עם 4 שכנים? (3⁴ = 81 במקום 3)
* האם 3,000 פרקים עדיין מספיקים לכסות אותו?
* זה בדיוק ה-trade-off שמתואר ב-[ADR-2](01_project_planning.md#adr-2-state-מקומי-בלבד-עומס-יוצא-ממוצע-3-דרגות).
</details>

### 3.3 Fallback בטוח
כשהסוכן במצב שלא נראה באימון (כל ה-Q = 0), השתמשו ב-`ShortestPathBaseline` במקום
שבירת שוויון לפי id. מדדו כמה החלטות כאלה יש בהערכה.

---

## 🔴 רמה 4: מחקר

### 4.1 מובהקות סטטיסטית
הריצו 10 seeds במקום 3, וחשבו paired t-test (או bootstrap CI) על הפרש ה-PDR בין
Q-learning ל-shortest path. האם ההפרש מובהק ב-p < 0.05?

### 4.2 כשל קישור
הוסיפו לסביבה אירוע: באמצע פרק, קישור (למשל Kansas City ↔ Indianapolis) נופל.
* איך shortest path מגיב? (ה-cache שלו כבר לא נכון!)
* איך הסוכן מגיב? הוא לא ראה את המצב הזה באימון.
* זה ה-"distribution shift" מ-[interview_guide](../interview_guide.md#5-failure-cases-worth-discussing).

### 4.3 סריקת עומס
הריצו את הניסוי עם `capacity_scale` ב-`[1.5, 1.2, 1.0, 0.8, 0.6]` וציירו גרף של
PDR(Q-learning) − PDR(shortest path) כפונקציה של העומס. באיזו נקודה הלמידה מתחילה
להשתלם?

---

## ✅ צ'קליסט לפני שמגישים שינוי

- [ ] `make test`: כל הבדיקות עוברות, כולל הבדיקות החדשות שלך
- [ ] `make lint`: נקי
- [ ] בדיקה חדשה לכל פונקציה חדשה, עם **מספרים מדויקים** ולא רק "שזה רץ"
- [ ] `make experiments`: 0 כשלים לסוכן, והתוצאות ב-README מעודכנות
- [ ] commit עם הודעה שמסבירה **למה** ולא רק **מה**

[⬅ תקלות ופתרונות](03_troubleshooting.md) · [חזרה לאזור הלמידה](README.md)
